from bs4 import BeautifulSoup, Tag
import ebooklib, json
from string import whitespace

def striper(string):
    string = string.replace('\n', ' ')
    if string.strip() == str():
        return str()
    else:
        res = string.strip()
        if string[0] in whitespace:
            res += ' '
        if string[len(string) - 1] in whitespace:
            res = ' ' + string
        return string

def justify_formated_string(string, target_line_length = 78):
    space = ('', ' ')
    doubleSpace = ('class:whitespace', '  ')
    string = remove_trailing_formated_whitespace(string)
    while string.count(space) > 0 and len_formated(string) < target_line_length:
        string[string.index(space)] = doubleSpace
    return string

def len_formated(list):
    res = 0
    for x in list:
        res += len(x[1])
    return res

def split_formated(text, split_by):
    res = []
    splited = text[1].split(split_by)
    for x in splited:
        if len(res) > 0:
            res.append(('', ' '))
        res.append((text[0], x))
    return res

def remove_trailing_formated_whitespace(list):
    if list[len(list) - 1][1] in whitespace and len(list) > 2:
        return list[:len(list) - 1]
    else:
        return list

class Chapter(object):
    """Parses chapter html into string or list of dicts"""
    def __init__(self,
            raw_,
            ignored_tags_ = [],
            paragraphTags_ = ['p', 'h1', 'h2', 'h3', 'dt', 'dd'],
            newlineTags_ = ['div'],
            lineLength = 78
        ):
        super(Chapter, self).__init__()
        """
            raw_ - raw html
            ignored_tags_ - list of tags to ignore and skip
            newlineTags_ - list of tags that should force newlines
            paragraphTags_ - list of tags that should be paragraphs
        """
        self.raw = raw_.decode('utf-8')
        self.soup = BeautifulSoup(self.raw, features='lxml')
        self.ignored_tags = ignored_tags_.copy()
        self.newlineTags = paragraphTags_.copy()
        self.specialNeedsTags = newlineTags_.copy()
        self.lineLength = lineLength
    def title(self):
        return self.soup.find('title')
    def hasBody(self):
        body = self.soup.find('body')
        if not body == None:
            if len(body.get_text().strip()) > 1:
                return True
        return False
    def contents(self):
        return self.stylisticSoupWalker(self.soup.find('body'))
    def stylisticSoupWalker(self, soup, allowed_to_insert_newlines = True):
        """
        soupWalker that returns a list of touples for prompt_toolkit
        text formating from epub's html.
        """
        res = list()
        # Walk through html tree
        for child in soup.children:
            # If tag -> walk over it's children and append the walking result
            if type(child) == Tag:
                if child.name not in self.ignored_tags:
                    # Get text from children
                    x = self.stylisticSoupWalker(child, not (child.name in self.newlineTags and allowed_to_insert_newlines))
                    if x != None or x[1] != str():
                        """
                            If the text is supposed to ba a paragraph -> make sure it is
                            surrounded by newlines
                        """
                        try:
                            if ((child.name in self.newlineTags and allowed_to_insert_newlines) or child.name in self.specialNeedsTags
                                ) and res[len(res) -1] != ('', '\n'):
                                res += [('', '\n')]
                        except:
                            pass
                        res += x
                        if child.name in self.newlineTags and allowed_to_insert_newlines:
                            res += [('', '\n')]
            # If the child is text -> append non-empty text
            else:
                if child.parent.name == 'span':
                    name = child.parent.parent.name
                else:
                    name = child.parent.name
                x = ('class:' + name, striper(child))
                if x[1] != str():
                    res.append(x)
        return res
    def text(self):
        """Returns text with basic formating"""
        res = str()
        a = self.wrapedContents()
        if a != None:
            for x in a[0]:
                res += x[1]
            if res.strip() == str():
                return 'Nothing here, empty chapter', list()
            else:
                return res, a[1]
        else:
            return 'Nothing here, empty chapter', list()
    def wrapedContents(self, preChar = ' '):
        """Returns a list of (style, text) touples of wrapped and justified text"""
        lineLength = self.lineLength
        breaks = [0]
        res = list()
        pseudoParagraphs = [[]]
        for text in self.contents():
            if text[1] != '\n':
                pseudoParagraphs[len(pseudoParagraphs) - 1].append(text)
            else:
                if not pseudoParagraphs[len(pseudoParagraphs) - 1] == []:
                    pseudoParagraphs.append([])
        newline = [('', '\n')]
        formated_preChar = [('class:preChar', preChar)]
        line_number = 0
        for paragraph in pseudoParagraphs:
            line = formated_preChar.copy()
            text = []
            for x in paragraph:
                for y in split_formated(x, ' '):
                    try:
                        last = text[len(text) - 1]
                    except:
                        last = None
                    if y[1] != '' and not (last == ('', ' ') and y == ('', ' ')):
                        text.append(y)
            for word in text:
                if len_formated(line + [word]) < lineLength:
                    line += [word]
                else:
                    res += justify_formated_string(line, lineLength) + newline
                    line = formated_preChar.copy()
                    line_number += 1
                    if word != ('', ' '):
                        line += [word]
            res += line + newline + newline
            line_number += 2
            breaks.append(line_number - 1)
        try:
            while res[len(res) - 1][1] in whitespace:
                res = res[:len(res) - 1]
        except:
            pass
        if res == newline:
            return None
        else:
            return res, breaks

if __name__ == '__main__':
    # Used for parser dubuging
    debug = True
    from ebooklib import epub
    testFile = 'The Rise of Kyoshi.epub'
    book = epub.read_epub(testFile)
    id = 0
    # Print chapter after chapter
    for x in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        print('\n------', id, '------\n')
        chapter = Chapter(x.content, ['sup'], lineLength = 80)
        print(chapter.hasBody())
        try:
            text, breaks = chapter.text()
            print(text[:2000])
        except:
            pass
        id += 1
        input()

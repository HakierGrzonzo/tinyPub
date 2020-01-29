from bs4 import BeautifulSoup, Tag
import ebooklib, json
import prompt_toolkit as pt

def striper(string):
    string = string.replace('\n', ' ')
    if string.strip() == str():
        return str()
    else:
        res = string.strip()
        if string.endswith(' '):
            res += ' '
        if string.startswith(' '):
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
    for x in range(len(list) - 2, -1, -1 ):
        if list[x][1].strip() == str():
            list.pop(x)
        else:
            break
    return list

class Chapter(object):
    """Parses chapter html into string or list of dicts"""
    def __init__(self,
            raw_,
            ignored_tags_ = [],
            newlineTags_ = ['p', 'h1', 'h2', 'h3', 'dt', 'dd']
        ):
        super(Chapter, self).__init__()
        """
            raw_ - raw html
            ignored_tags_ - list of tags to ignore and skip
            newlineTags_ - list of tags that should be paragraphs
        """
        self.raw = raw_.decode('utf-8')
        self.soup = BeautifulSoup(self.raw, features='lxml')
        self.ignored_tags = ignored_tags_
        self.newlineTags = newlineTags_
        self.contents = self.stylisticSoupWalker(self.soup)
    def stylisticSoupWalker(self, soup, allowed_to_insert_newlines = True):
        """
        soupWalker that returns a list of touples for prompt_toolkit
        text formating.
        """
        res = list()
        for child in soup.children:
            if type(child) == Tag:
                if child.name not in self.ignored_tags:
                    x = self.stylisticSoupWalker(child, not (child.name in self.newlineTags and allowed_to_insert_newlines))
                    if x != None or x[1] != str():
                        res += x
                        if child.name in self.newlineTags and allowed_to_insert_newlines:
                            res += [('', '\n')]
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
        res = str()
        a = self.wrapedContents()
        if a != None:
            for x in a[0]:
                res += x[1]
            if res.strip() == str():
                return None
            else:
                return res, a[1]
        else:
            return None
    def wrapedContents(self, lineLength = 78, preChar = ' '):
        breaks = list()
        res = list()
        pseudoParagraphs = [[]]
        for text in self.contents:
            if text[1] != '\n':
                pseudoParagraphs[len(pseudoParagraphs) - 1].append(text)
            else:
                if not pseudoParagraphs[len(pseudoParagraphs) - 1] == []:
                    pseudoParagraphs.append([])
        newline = [('', '\n')]
        formated_preChar = [('class:preChar', preChar)]
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
                    res += justify_formated_string(line) + newline
                    line = formated_preChar.copy()
                    if word != ('', ' '):
                        line += [word]

            res += line + newline + newline
            breaks.append(len_formated(res) - 1)
        res = remove_trailing_formated_whitespace(res)
        breaks = breaks[:len(breaks) - 2]
        breaks.append(len_formated(res) - 2)
        if res == newline:
            return None
        else:
            return res, breaks
    def formatedText(self):
        text = self.wrapedContents()
        if text == None:
            return None
        else:
            return pt.formatted_text.to_formatted_text(text[0]), text[1]

defaultStyle = pt.styles.Style.from_dict({
        'em': 'bold',
        'h1': 'bold',
        'h2': 'bold',
        'blockquote': 'italic'
    })

if __name__ == '__main__':
    debug = True
    from ebooklib import epub
    testFile =  'test.epub'
    book = epub.read_epub(testFile)
    id = 0

    for x in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        print('\n------', id, '------\n')
        chapter = Chapter(x.get_body_content(), ['sup'])
        text, breaks = chapter.formatedText()
        pt.print_formatted_text(text, style = defaultStyle)
        #print(json.dumps(text, indent = 4))
        id += 1
        input()

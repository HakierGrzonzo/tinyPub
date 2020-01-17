from bs4 import BeautifulSoup
import ebooklib

debug = False
listOfTagsThatHaveNewLines = ['p', 'h1', 'h2', 'h3', 'dt']

def wraper(text, line_length = 78, pre_char = ' ', indent = '', generate_breaks = False):
    res = str()
    breaks = list()
    for paragraph in text.split('\n'):
        par = indent
        line = pre_char + par
        for word in paragraph.split(' '):
            if len(line + word) > line_length:
                par += line + '\n'
                line = pre_char + word + ' '
            else:
                line += word.strip() + ' '
        par += line + '\n'
        res += par + '\n'
        breaks.append(len(res) - 1)
    try:
        breaks = breaks[:len(breaks) - 2].copy()
        breaks[len(breaks) - 1] = len(pre_char + indent + res.strip())
    except:
        breaks = []
    if generate_breaks:
        return pre_char + indent + res.strip(), breaks
    else:
        return pre_char + indent + res.strip()

def soupWalker(soup, is_paragraph = False, ignore = []):
    """is_paragraph is for internal use only, do not use it while calling
    the function"""
    if soup.name in ignore:
        return str()
    try:
        result = str()
        for child in soup.contents:
            if child.name in listOfTagsThatHaveNewLines and not is_paragraph:
                ending = '\n'
                is_local_paragraph = True
            else:
                ending = ''
                is_local_paragraph = False
            res = soupWalker(child, is_local_paragraph, ignore) + ending
            if len(res.strip()) > 0:
                result += res
        return result
    except Exception as e:
        if soup.string.find('\n') != -1:
            result = str()
            for x in soup.string.split('\n'):
                result += x.strip() + ' '
            return result
        else:
            return str(soup.string)

def parse(chapter, ignore = []):
    soup = BeautifulSoup(chapter.get_body_content().decode('utf-8'), features='lxml')
    test = soupWalker(soup.find('body'), ignore = ignore)
    if len(test.strip()) == 0:
        return None
    else:
        return test


if __name__ == '__main__':
    debug = True
    from ebooklib import epub
    testFile =  'lalka.epub'
    book = epub.read_epub(testFile)
    id = 0
    for x in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        print(wraper(parse(x, ['sup']), generate_breaks = True))
        id += 1
        input()

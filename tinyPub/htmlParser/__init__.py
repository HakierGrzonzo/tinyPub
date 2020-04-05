from bs4 import BeautifulSoup, Tag
from .styles import StyleHandler, baseStyle, ppStyle
from .renderer import render, debug_printer
from ebooklib import epub
import ebooklib, json
from string import whitespace

def space_count(string):
    if string.strip() == str():
        return 999
    i = 0
    for char in string:
        if char in whitespace:
            i += 1
        else:
            break
    return i

class Chapter(object):
    """Parses chapter html to raw text.

    Parameters
    ==========
        raw_: bytes
            html in bytes (utf-8)
        ignored_tags_: list of str
            tags that will be ignored with their children
        lineLength: int
            target max lineLength
        css_data: list of Style
            list with style objects to be used
        """

    def __init__(self,
            raw_,
            ignored_tags_ = [],
            lineLength = 78,
            css_data = dict()):
        super(Chapter, self).__init__()
        self.ignored_tags = ignored_tags_
        self.soup = BeautifulSoup(raw_.decode('utf-8'), features='lxml')
        self.width = lineLength
        self.css = baseStyle.copy()
        for link in self.soup.find_all('link'):
            self.css.overwrite(css_data.get(link.get('href')))
    def title(self):
        return self.soup.find('title')
    def hasBody(self):
        body = self.soup.find('body')
        if not body == None:
            if len(body.string.strip()) > 1:
                return True
        return False
    def contents(self):
        return self.soup.find('body')
    def render(self):
        return render(self.contents(), self.css, self.width, ignored_tags=self.ignored_tags)
    def text(self):
        """returns text from render() and generates breaks"""
        text = self.render()
        lines = text.split('\n')
        breaks = list()
        rising_edge = True
        for i in range(len(lines)):
            try:
                if rising_edge:
                    if space_count(lines[i]) > space_count(lines[i+1]):
                        rising_edge = False
                        breaks.append(i)
                    i += 1
                else:
                    if space_count(lines[i]) < space_count(lines[i+1]):
                        rising_edge = True
                    i += 1
            except IndexError:
                break
        breaks.append(len(lines) - 1)
        return text, breaks




if __name__ == '__main__':
    import sys
    book = epub.read_epub(sys.argv[1])
    styles = dict()
    for x in book.get_items_of_type(ebooklib.ITEM_STYLE):
        styles[x.file_name] = StyleHandler(x.get_content())
    for x in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        chapter = Chapter(x.content, css_data = styles, width = 78, ignored_tags_ = ['sup'])
        chapter.text()

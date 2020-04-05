import cssutils, json
from pprint import pprint as pp
from .default import default
import logging, copy

max_vertical_margin_size = 2

def ppStyle(style):
    style = copy.deepcopy(style.styleDict)
    res = dict()
    for k, v in style.items():
        if v.get('margins') != None:
            v['margins'] = v['margins'].__str__()
        res[k.__str__()] = v
    pp(res)

handledProperties = [
    'border',
    'text-align',
    'font-style',
    'font-weight',
    'display',
    'text-indent'
]

def separateUnit(string):
    nums = ['.'] + [str(x) for x in range(10)]
    num_str = str()
    unit_str = str()
    for i in range(len(string)):
        if string[i] not in nums:
            num_str = string[:i-1]
            unit_str = string[i-1:]
    if num_str == str():
        num_str = string
    return float(num_str), unit_str

def unitConverter(entry):
    entry = str(entry)
    try:
        if entry.strip() in ['0', 'auto', None, str()]:
            return 0
        unit_to_char_dict = {
            'em': 2,
            'ex': 1,
            'ch': 1,
            'rem': 2,
            'cm': 5,
            'mm': 0.5,
            'in': 12.7,
            'px': 0.13,
            'pt': 0.18,
            'pc': 0.014
        }
        num, unit = separateUnit(entry.strip())
        try:
            return round(num * unit_to_char_dict[unit])
        except KeyError:
            return 0
    except ValueError:
        return 0

class Margins:
    """class that contains and preprocesses entries for margins"""
    def __init__(self, raw_margins_dict = None, top = 0, bottom = 0, right = 0, left = 0):
        self.top = top
        self.bottom = bottom
        self.right = right
        self.left = left
        if raw_margins_dict != None:
            # handle 'margin'
            if raw_margins_dict.get('margin') != None:
                data = [unitConverter(x) for x in raw_margins_dict['margin'].strip().split(' ')]
                try:
                    self.top += data[0]
                    self.right += data[1]
                    self.bottom += data[2]
                    self.left += data[3]
                except IndexError:
                    pass
            # handle margin-left, margin-bottom etc.
            self.top += unitConverter(raw_margins_dict.get('margin-top', 0))
            self.bottom += unitConverter(raw_margins_dict.get('margin-bottom', 0))
            self.left += unitConverter(raw_margins_dict.get('margin-left', 0))
            self.right += unitConverter(raw_margins_dict.get('margin-right', 0))
            # handle margin-block-… and margin-inline-…
            self.top += unitConverter(raw_margins_dict.get('margin-block-start', 0))
            self.bottom += unitConverter(raw_margins_dict.get('margin-block-end', 0))
            self.left += unitConverter(raw_margins_dict.get('margin-inline-start', 0))
            self.right += unitConverter(raw_margins_dict.get('margin-inline-end', 0))
        self.top = min(max_vertical_margin_size, self.top)
        self.bottom = min(max_vertical_margin_size, self.bottom)
    def __str__(self):
        return str(self.top) + ' ' + str(self.right) + ' ' + str(self.bottom) + ' ' + str(self.left)

class style_selector(object):
    """docstring for style_selector."""

    def __init__(self, tag = None, class_ = None, tagName = None):
        super(style_selector, self  ).__init__()
        if tag != None:
            self.class_ = tag.get('class')[0]
            self.tagName = None
        else:
            self.class_ = class_
            self.tagName = tagName
    def __eq__(self, other):
        return self.class_ == other.class_ and self.tagName == other.tagName
    def __hash__(self):
        return hash((self.class_, self.tagName))
    def __str__(self):
        return str(self.tagName) + '.' + str(self.class_)

def style_to_dict(styleString) -> dict:
    res = dict()
    if isinstance(styleString, bytes):
        styleString = styleString.decode('utf-8')
    cssutils.log.setLevel(logging.CRITICAL)
    sheet = cssutils.parseString(styleString)
    for rule in sheet:
        ruleDict = dict()
        try:
            for property in rule.style:
                if property.name in handledProperties or property.name.find('margin') != -1:
                    ruleDict[property.name] = property.value
            if ruleDict != dict():
                res[rule.selectorText] = ruleDict
        except AttributeError as e:
            pass
    styleDict = dict()
    for selector, style in res.items():
        selectors = [x.strip() for x in selector.split(',')]
        for select in selectors:
            if select.find(' ') == -1 and select.find('>') == -1:
                if select.find('.') != -1:
                    tag, class_ = select.split('.')
                    if tag == str():
                        tag = None
                else:
                    tag = select
                    class_ = None
                styleselector = style_selector(tagName = tag, class_ = class_)
                if styleDict.get(styleselector) != None:
                    for k, v in styleDict[styleselector].items():
                        style[k] = v
                styleDict[styleselector] = style
    return styleDict

class StyleHandler(object):
    """docstring for StyleHandler."""
    def __init__(self, styleString = str(), styleDict = dict()):
        super(StyleHandler, self).__init__()
        if styleDict == dict():
            self.styleDict = style_to_dict(styleString)
        else:
            self.styleDict = styleDict
    def overwrite(self, other):
        """overwrites values in self with values in other"""
        if isinstance(other, StyleHandler):
            for k, v in other.styleDict.items():
                if self.styleDict.get(k) == None:
                    self.styleDict[k] = v
                else:
                    base = self.styleDict[k]
                    for key, value in v.items():
                        base[key] = value
                    self.styleDict[k] = base

    def get(self, tag):
        style = self.styleDict.get(style_selector(tagName = tag.name), dict())
        # get styles according to class
        if tag.get('class') != None:
            for k, v in self.styleDict.get(style_selector(class_ = tag.get('class', None)[0]), dict()).items():
                style[k] = v
            for k, v in self.styleDict.get(style_selector(tag = tag), dict()).items():
                style[k] = v
        style['margins'] = Margins(style)
        return style
    def copy(self):
        return StyleHandler(styleDict = copy.deepcopy(self.styleDict))

baseStyle = StyleHandler(default)

if __name__ == '__main__':
    import ebooklib, sys
    from bs4 import BeautifulSoup as Soup
    from ebooklib import epub
    book = epub.read_epub(sys.argv[1])
    for x in book.get_items_of_type(ebooklib.ITEM_STYLE):
        style = StyleHandler(x.get_content())
        baseStyle.overwrite(style)
    ppStyle(baseStyle)

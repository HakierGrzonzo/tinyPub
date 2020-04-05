from .styles import Margins, unitConverter
from bs4 import Tag
from .textFormater import bold, italic

def debug_printer(item):
    if isinstance(item, element):
        res = '<{0}>:'.format(item.type)
        for x in item.children:
            res += '\n\t' + debug_printer(x).replace('\n', '\n\t')
        return res
    else:
        return 'text: ' + item.string.replace(' ', '_')



class text():
    """docstring for text."""
    def __init__(self, string, style):
        if style.get('font-weight') == 'bold':
            string = bold(string)
        if style.get('font-style') in ['oblique', 'italic']:
            string = italic(string)
        try:
            string = string.replace('\t', ' ')
        except:
            pass
        self.string = string
    def render(self, force_inline = False):
        return self.string

def len_str_list(lis):
    res = 0
    for x in lis:
        res += len(lis)
    return res

class element():
    """Represents any `display-type: block;`
        has nested in-line elements or blocks"""
    def __init__(self, tag, stylesheet, rootWidth, minimal_content_width = 5, tags_to_ignore = []):
        self.style = stylesheet.get(tag)
        self.margins = self.style.get('margins', Margins())
        self.type = self.style.get('display', 'in-line')
        self.children = list()
        self.width = rootWidth
        self.minimal_content_width = minimal_content_width
        for child in tag.children:
            if isinstance(child, Tag):
                if tag.name not in tags_to_ignore:
                    self.children.append(element(child, stylesheet, self.content_width(), tags_to_ignore = tags_to_ignore))
            else:
                if len(child.strip()) > 0:
                    self.children.append(text(child, self.style))
    def content_width(self):
        x = self.width - self.margins.left - self.margins.right
        if x > self.minimal_content_width:
            return x
        else:
            return self.minimal_content_width
    def make_paragraph(self, text_children):
        if len(text_children) > 0:
            # handle text_children
            text = str()
            for child in text_children:
                text += child.render()
            text = [x.strip() for x in text.split('\n')]
            text_str = str()
            for x in text:
                text_str += x + ' '
            text_str = text_str[:len(text_str) -1]
            i = 0
            while True:
                try:
                    if text_str[i] == ' ' and text_str[i+1] == ' ':
                        text_str = text_str[:i] + text_str[i:]
                    i += 1
                except IndexError:
                    break
            # wrap the text into a paragraph
            lines = list()
            # set first line to indent
            current_line = ' ' * unitConverter(self.style.get('text-indent'))
            for word in text_str.split(' '):
                if len(current_line) + len(word) + 1 < self.content_width():
                    current_line += ' ' + word
                else:
                    lines.append(current_line)
                    current_line = word
            lines.append(current_line)
            alingment = self.style.get('text-align')
            if alingment == 'center':
                lines = [x.center(self.content_width()) for x in lines]
            elif alingment == 'right':
                lines = [x.rjust(self.content_width()) for x in lines]
            elif alingment == 'justify':
                new_lines = list()
                for line in lines[:len(lines) - 1]:
                    line = line.split(' ')
                    i = 0
                    while len_str_list(line) + len(line) - 1 < self.content_width():
                        try:
                            line[i] += ' '
                            i += 1
                        except IndexError:
                            break
                    new_line = str()
                    for word in line[:len(line) - 1]:
                        new_line += word + ' '
                    new_line += line[len(line) - 1]
                    new_lines.append(new_line)
                new_lines.append(lines[len(lines) - 1])
                lines = new_lines
            elif alingment == 'left':
                lines = [x.ljust(self.content_width()) for x in lines]
            res = str()
            for line in lines:
                res += line + '\n'
            return res
        else:
            return str()
    def render(self, force_inline = False):
        if self.type == 'in-line' or force_inline:
            text_str = str()
            for child in self.children:
                post_render = child.render(force_inline = True)
                if isinstance(post_render, text):
                    text_str += post_render.render()
                else:
                    text_str += post_render
            return text(text_str, self.style)
        elif self.type in ['block', 'list-item']:
            result = str()
            text_children = list()
            last_margin_bottom_len = 0
            for child in self.children:
                if isinstance(child, text):
                    text_children.append(child)
                elif child.type == 'in-line':
                    text_children.append(child.render())
                else:
                    post_render = child.render()
                    result += self.make_paragraph(text_children)
                    text_children = list()
                    if isinstance(post_render, text):
                        post_render = child.make_paragraph([post_render])
                        # add side margins to child
                        post_render = ' '*child.margins.left + post_render.replace('\n', ' '*child.margins.right + '\n' + ' '*child.margins.left, post_render.count('\n') - 1)

                    result += '\n'*max(last_margin_bottom_len, child.margins.top) + post_render
                    last_margin_bottom_len = child.margins.bottom
            result += self.make_paragraph(text_children)
            # add side margins
            result = ' '*self.margins.left + result.replace('\n', ' '*self.margins.right + '\n' + ' '*self.margins.left, result.count('\n') - 1)
            #print(self.style, '\n', result.replace(' ', '~'), '\n', self.margins, '\n----\n')
            return result
        else:
            return str()

def render(body, styleDict, rootWidth, ignored_tags = []):
    x = element(body, styleDict, rootWidth, tags_to_ignore = ignored_tags)
    return x.render()

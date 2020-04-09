from .styles import Margins, unitConverter
from bs4 import Tag
from .textFormater import bold, italic, justify

def debug_printer(item):
    """returns a nice string representationof element() tree, for debugging"""
    if isinstance(item, element):
        res = '<{0}>:'.format(item.type)
        for x in item.children:
            res += '\n\t' + debug_printer(x).replace('\n', '\n\t')
        return res
    else:
        return 'text: ' + item.string.replace(' ', '_')



class text():
    """changes "font" in 'string' according to rules in 'style'"""
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
        """force_inline is unused, returns self.string"""
        return self.string

class element():
    """Represents any block elements in html
        has nested in-line elements or blocks"""
    def __init__(self, tag, stylesheet, rootWidth, minimal_content_width = 5, tags_to_ignore = []):
        """
            Parameters
            ----------
            tag: bs4.Tag
                a tag to build the tree from
            stylesheet: StyleHandler
                used for representing css rules
            rootWidth: int
                width of the viewport in terminal
            minimal_content_width: int
                minimal width for block elements
            tags_to_ignore: list of str
                list of tags names to ignore
        """
        # get style, margins and 'display' for tag
        self.style = stylesheet.get(tag)
        self.margins = self.style.get('margins', Margins())
        # if no display was specified → assume in-line
        self.type = self.style.get('display', 'in-line')
        self.children = list()
        self.width = rootWidth
        self.minimal_content_width = minimal_content_width
        # Generate tree
        for child in tag.children:
            # handle Tags
            if isinstance(child, Tag):
                if tag.name not in tags_to_ignore:
                    self.children.append(element(child, stylesheet, self.content_width(), tags_to_ignore = tags_to_ignore))
            # handle text nodes
            else:
                # ignore blank ones
                if len(child.strip()) > 0:
                    self.children.append(text(child, self.style))
    def content_width(self):
        # Returns maximal width for content with margins
        x = self.width - self.margins.left - self.margins.right
        if x > self.minimal_content_width:
            return x
        else:
            return self.minimal_content_width
    def make_paragraph(self, text_children):
        """
            returns str of paragraph made from list of Text

            text_children: list of Text
        """
        if len(text_children) > 0:
            # Render Text in text_children to string
            text = str()
            for child in text_children:
                text += child.render()
            # HTML whitespace handling:
            # strip text for paragraph and remove spaces around newlines
            text = [x.strip() for x in text.split('\n')]
            text_str = str()
            # convert newlines to spaces
            for x in text:
                text_str += x + ' '
            # remove the space at the end
            text_str = text_str[:len(text_str) -1]
            # remove reapeating spaces
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
            # separate words
            for word in text_str.split(' '):
                # if fits in line → append to line
                if len(current_line) + len(word) + 1 < self.content_width():
                    current_line += ' ' + word
                # else → start new line
                else:
                    lines.append(current_line)
                    current_line = word
            # append line that was left at the end
            lines.append(current_line)
            # handle text alingment
            alingment = self.style.get('text-align', 'justify')
            if alingment == 'center':
                lines = [x.center(self.content_width()) for x in lines]
            elif alingment == 'right':
                lines = [x.rjust(self.content_width()) for x in lines]
            elif alingment == 'justify':
                lines = justify(lines, self.content_width())
            elif alingment == 'left':
                lines = [x.ljust(self.content_width()) for x in lines]
            # convert lines to one string
            res = str()
            for line in lines:
                res += line + '\n'
            return res
        else:
            return str()
    def render(self, force_inline = False):
        """Returns rendered block as str, or rendered text/inline element as Text
        
            Parameters
            ----------
            force_inline: bool
                internal parameter to ignore block elements in inline elements
        """
        if self.type == 'in-line' or force_inline:
            # handle inline elements
            text_str = str()
            for child in self.children:
                post_render = child.render(force_inline = True)
                # render Text to str
                if isinstance(post_render, text):
                    text_str += post_render.render()
                # append str
                else:
                    text_str += post_render
            # return as Text, to force formating
            return text(text_str, self.style)
        elif self.type in ['block', 'list-item']:
            # handle block elements
            # TODO: list-item handling
            result = str()
            text_children = list()
            # used for margin overlapping
            last_margin_bottom_len = 0
            for child in self.children:
                # append inline elements/Text to text_children to make_pargraph later
                if isinstance(child, text):
                    text_children.append(child)
                elif child.type == 'in-line':
                    text_children.append(child.render())
                else:
                    # make_paragraph from text_children
                    post_render = child.render()
                    result += self.make_paragraph(text_children)
                    text_children = list()
                    # make_paragraph from nested block element
                    if isinstance(post_render, text):
                        # if it renders to Text → make_paragraph to str
                        post_render = child.make_paragraph([post_render])
                        # add side margins to child
                        post_render = ' '*child.margins.left + post_render.replace('\n', ' '*child.margins.right + '\n' + ' '*child.margins.left, post_render.count('\n') - 1)
                    # else the rendering was done
                    # append the rendered block-element to result with overlapping margins
                    result += '\n'*max(last_margin_bottom_len, child.margins.top) + post_render
                    last_margin_bottom_len = child.margins.bottom
            # add last paragraph
            result += self.make_paragraph(text_children)
            # add side margins
            result = ' '*self.margins.left + result.replace('\n', ' '*self.margins.right + '\n' + ' '*self.margins.left, result.count('\n') - 1)
            #print(self.style, '\n', result.replace(' ', '~'), '\n', self.margins, '\n----\n')
            return result
        else:
            return str()

def render(body, styleDict, rootWidth, ignored_tags = []):
    """
        returns rendered html

        Parameters
        ----------
        body: bs4.Tag
            body tag from html document
        styleDict: StyleHandler
            style data for the document
        rootWidth: int
            width of the viewport
        tags_to_ignore: list of str
            list of tag names to ignore
    """
    x = element(body, styleDict, rootWidth, tags_to_ignore = ignored_tags)
    return x.render()

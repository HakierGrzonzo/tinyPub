#!/usr/bin/env python3
"""
A python .epub ebook reader
Used to be based on prompt_toolkit, but since version 1.9 is based on py_cui.
"""
from .htmlParser import Chapter, StyleHandler
import py_cui as pycui
from ebooklib import epub
import json, os, ebooklib, argparse
from multiprocessing import Pool, cpu_count
from .navParser import parse_navigation

__version__ = '2.0'
# Debug functions
log = list()
def pp(arg):
    print(json.dumps(arg, indent = 4))

class Addnotation():
    """Represents adnotation

    Parameters
    ----------
    breaks: list
        list containing paragraph breaks, so each adnotation is bound to paragraph
    text: str
        text for addnotation
    position: int
        cursor_text_pos_y form Displayer()
    dict: dict
        can be used instead of text&position, used for loading from config
    """
    def __init__(self, breaks, text = str(), position = -1, dict = dict()):
        """constructor for Addnotation()"""
        self.text = dict.get('text', text)
        pos = 0
        if position != -1:
            i = 1
            while True:
                if breaks[i] > position:
                    pos = i - 1
                    break
                i += 1
        self.pos = dict.get('position', pos)
        self.breaks = breaks
    def raw_pos(self):
        """converts relative pos to cursor_text_pos_y for use in Displayer()"""
        return self.breaks[self.pos]
    def dump(self):
        """converts addnotation to dict for storage"""
        return {'position': self.pos, 'text': self.text}


class impPYCUI(pycui.PyCUI):
    """py_cui.PyCUI but with add methods for mine classes"""
    def __init__(self, arg1, arg2):
        super(impPYCUI, self).__init__(arg1, arg2)
    def add_Displayer(self, title, row, column, row_span = 1, column_span = 1, padx = 1, pady = 0, book = None):
        id = 'Widget{}'.format(len(self.widgets.keys()))
        new_displayer = Displayer(id, title,  self.grid, row, column, row_span, column_span, padx, pady, book)
        self.widgets[id] = new_displayer
        if self.selected_widget is None:
            self.set_selected_widget(id)
        return new_displayer
    def add_Adnotation_menu(self, title, row, column, row_span = 1, column_span = 1, padx = 1, pady = 0):
        id = 'Widget{}'.format(len(self.widgets.keys()))
        new_adnotation_menu = Adnotation_menu(id, title, self.grid, row, column, row_span, column_span, padx, pady)
        self.widgets[id] = new_adnotation_menu
        if self.selected_widget is None:
            self.set_selected_widget(id)
        return new_adnotation_menu

class Adnotation_menu(pycui.widgets.ScrollMenu):
    """ScrollMenu but with methods to return objects form dict"""
    def __init__(self, id, title, grid, row, column, row_span, column_span, padx, pady):
        super(Adnotation_menu, self).__init__(id, title, grid, row, column, row_span, column_span, padx, pady)
        # Dict for: entry in ScrollMenu -> object
        self.decoding_dict = dict()
        self.Displayer = None
        self.set_focus_text('Press enter to jump to selected item.')
    def add_adnotation(self, adnotation):
        """Adds Addnotation() to menu, sorts addnotations based on position"""
        adnotations = list([self.decoding_dict[v] for v in self.get_item_list()])
        adnotations.append(adnotation)
        adnotations.sort(key = lambda item: item.pos)
        self.decoding_dict = dict()
        res = list()
        for a in adnotations:
            text = str(len(res) + 1) + '. ' + a.text
            self.decoding_dict[text] = a
            res.append(text)
        self.clear()
        self.add_item_list(res)
    def handle_adnotation(self):
        """Returns selected Addnotation()"""
        adnotation = self.decoding_dict[self.get()]
        self.Displayer.jump_to_line(adnotation.raw_pos())

class Displayer(pycui.widgets.ScrollTextBlock):
    """basicly py_cui Text_block that is read only and has some glue for Book()"""
    def __init__(self, id, title, grid, row, column, row_span, column_span, padx, pady, book):
        global config
        self.book = book
        # set title according to book's chapter title
        text, self.breaks, self.title = self.book.chapter_returner()
        # pass all parameters and chapter's text to parent class
        super(Displayer, self).__init__(id, self.title, grid, row, column, row_span, column_span, padx, pady, text)
        # get keybindings from config, I know it is not supposed to work like that, but it works
        self.keybinds = config.get('keybindings', {'h': 'prev', 'j': 'down', 'k': 'up', 'l': 'next'})
        self.addnotationDisplayer = None
        # Set help text
        reverseKeybinds = dict()
        for k, v in self.keybinds.items():
            reverseKeybinds[v] = k
        self.set_focus_text('t - Table of contents | ' + reverseKeybinds['prev'] + ', ' + reverseKeybinds['next'] + ' - change chapter | a - add note on cursor | ' + reverseKeybinds['up'] + ', ' + reverseKeybinds['down'] + ' - fast scroll | Esc - select widget')
        # set initial cursor position according to saved entry in config
        last = None
        while self.cursor_text_pos_y < self.book.XcursorPos:
            last = self.cursor_text_pos_y
            self.move_down()
            if last == self.cursor_text_pos_y:
                # if cursor position is  not changing, well, you tried
                break
        while self.cursor_text_pos_x < self.book.YcursorPos:
            last = self.cursor_text_pos_x
            self.move_right()
            if last == self.cursor_text_pos_x:
                break
    def insert_char(self, key_pressed):
        """hijack insert_char to handle some keybindings"""
        action = self.keybinds.get(chr(key_pressed))
        if action == 'prev':
            # switch chapter to previous one
            text, self.breaks, self.title = self.book.select_prev_chapter()
            self.set_text(text)
            self.load_adnotations()
        if action == 'next':
            # switch chapter to next one
            text, self.breaks, self.title = self.book.select_next_chapter()
            self.set_text(text)
            self.load_adnotations()
        # jump to paragraph break
        if action == 'down':
            for x in self.breaks:
                if x > self.cursor_text_pos_y:
                    self.jump_to_line(x)
                    break
        if action == 'up':
            for x in self.breaks[::-1]:
                if x < self.cursor_text_pos_y:
                    self.jump_to_line(x)
                    break
    def handle_delete(self):
        pass
    def handle_backspace(self):
        pass
    def handle_newline(self):
        pass
    def load_adnotations(self):
        """load notifications after self.addnotationDisplayer is set and after chapter change"""
        if self.addnotationDisplayer == None:
            return
        self.addnotationDisplayer.clear()
        for x in self.book.addnotations:
            # add notifications from entry in config
            self.addnotationDisplayer.add_adnotation(x)
    def add_adnotation_on_cursor(self, text):
        """adds addnotation in paragraph where cursor is located"""
        adnotation = self.book.add_adnotation(text, self.cursor_text_pos_y, self.breaks)
        if not self.addnotationDisplayer == None:
            self.addnotationDisplayer.add_adnotation(adnotation)
    def getTOC(self):
        """generates dict: TOC entry -> chapterIndex for Book()"""
        res = dict()
        i = 1
        for item in self.book.chapters:
            res[str(i) + '. ' + item['title']] = i
            i += 1
        return res
    def force_chapter(self, identifier):
        """change chapter to identifier"""
        try:
            num = self.getTOC()[identifier] - 1
            text, self.breaks, self.title = self.book.select_chapter(num)
            self.set_text(text)
            self.load_adnotations()
        except Exception as e:
            global log
            log.append('force_chapter: ' + str(e))
    def jump_to_line(self, line):
        """change cursor_text_pos_y to line"""
        if self.cursor_text_pos_y > line:
            last = self.cursor_text_pos_y
            while line < self.cursor_text_pos_y:
                last = self.cursor_text_pos_y
                self.move_up()
                if last == self.cursor_text_pos_y:
                    # if position has not changed, abort
                    break
        elif self.cursor_text_pos_y < line:
            last = self.cursor_text_pos_y
            while self.cursor_text_pos_y < line:
                last = self.cursor_text_pos_y
                self.move_down()
                if last == self.cursor_text_pos_y:
                    # if position has not changed, abort
                    break

class Book(object):
    """A wrapper class that represents ebook with its htmlParser.chapter-s and addnotations

    Parameters
    ----------
    pathToFile: str
        path to .epub file"""
    def __init__(self, pathToFile):
        global config
        super(Book, self).__init__()
        # try to load epub from pathToFile
        try:
            self.book = epub.read_epub(pathToFile)
        except Exception as e:
            raise ValueError('Exception while importing epub:', str(e))
        # initialize chapters in dict: file_name_in_epub -> chapter
        chapters = dict()
        styles = dict()
        for x in self.book.get_items_of_type(ebooklib.ITEM_STYLE):
            styles[x.file_name] = StyleHandler(x.get_content())
        for item in self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            chapter = Chapter(item.content, ['sup'], lineLength = config.get('lineLength', 78), css_data = styles)
            # ignore empty ones
            if chapter.hasBody:
                chapters[item.file_name] = chapter
        # order chapters according to toc.ncx in epub
        try:
            navigation = list(self.book.get_items_of_type(ebooklib.ITEM_NAVIGATION))[0]
            self.navigation = parse_navigation(navigation.content)
            self.chapters = list()
            for entry in self.navigation:
                try:
                    entry['chapter'] = chapters[entry['content']]
                    self.chapters.append(entry)
                except KeyError:
                    pass
        # If that is not possible, fall back on just trusting ebooklib
        except Exception as e:
            self.chapters = list()
            for chapter in chapters:
                x = dict()
                x['chapter'] = chapter
                self.chapters.append(x)
        # set inital chapter and cursor position according to config entry
        self.configEntry = config.get('books').get(self.title(), dict())
        self.chapterIndex = int(self.configEntry.get('chapter', 1))
        self.XcursorPos = self.configEntry.get('cursorX', 0)
        self.YcursorPos = self.configEntry.get('cursorY', 0)
    def chapter_returner(self):
        """returns text, paragraph breaks and title of current chapter. Also initializes
        addnotations for current chapter"""
        text, breaks = self.chapters[self.chapterIndex]['chapter'].text()
        addnotations = self.configEntry.get('addnotations', dict()).get(str(self.chapterIndex), list())
        self.addnotations = [Addnotation(breaks, dict = x) for x in addnotations]
        return text, breaks, self.chapters[self.chapterIndex]['title']
    def title(self):
        """returns book's title"""
        return self.book.get_metadata('DC', 'title')[0][0]
    def select_chapter(self, new_chapter_num):
        """selects chapter number new_chapter_num, then exceutes chapter_returner() and returns its
        results"""
        if new_chapter_num < 0 or new_chapter_num > len(self.chapters) - 1:
            raise ValueError('Chapter does not exist')
        try:
            self.configEntry['addnotations'][str(self.chapterIndex)] = [x.dump() for x in self.addnotations]
        except:
            self.configEntry['addnotations'] = dict()
            self.configEntry['addnotations'][str(self.chapterIndex)] = [x.dump() for x in self.addnotations]
        self.chapterIndex = new_chapter_num
        self.XcursorPos = 0
        self.YcursorPos = 0
        return self.chapter_returner()
    def select_next_chapter(self):
        """tries to select next chapter"""
        try:
            return self.select_chapter(self.chapterIndex + 1)
        except Exception as e:
            return self.chapter_returner()
    def select_prev_chapter(self):
        """tries to select previous chapter"""
        try:
            return self.select_chapter(self.chapterIndex - 1)
        except Exception as e:
            return self.chapter_returner()
    def add_adnotation(self, text, y_pos, breaks):
        """adds addnotation created from arguments to config entry and
        returns coresponding Addnotation()"""
        res = Addnotation(breaks, text = text, position = y_pos)
        self.addnotations.append(res)
        return res
    def dump_to_config(self, YcursorPos, XcursorPos):
        """commits changes to its config entry"""
        global config
        try:
            self.configEntry['addnotations'][str(self.chapterIndex)] = [x.dump() for x in self.addnotations]
        except:
            self.configEntry['addnotations'] = dict()
            self.configEntry['addnotations'][str(self.chapterIndex)] = [x.dump() for x in self.addnotations]
        self.configEntry = {
            'chapter': self.chapterIndex,
            'cursorX': XcursorPos,
            'cursorY': YcursorPos,
            'addnotations': self.configEntry.get('addnotations', dict())
        }
        config['books'][self.title()] = self.configEntry

class Interface:
    """base interface class, initializes interface with book"""
    def __init__(self, master, book):
        self.master = master
        self.book = book
        self.master.toggle_unicode_borders()
        # set application title to book's title
        self.master.set_title(self.book.title())
        self.master.grid.offset_x = 0
        self.master.grid.offset_y = 0
        # calculate width for given lineLength in config for Displayer()
        lineLength = config.get('lineLength', 78)
        min_columns = (lineLength + 15) // self.master.grid.column_width + 1
        try:
            self.textDisplayer = self.master.add_Displayer('' ,row = 0, column = 0, row_span = 5, column_span = min_columns, book = self.book)
        except:
            self.textDisplayer = self.master.add_Displayer('' ,row = 0, column = 0, row_span = 5, column_span = self.master.grid.num_columns, book = self.book)
        if min_columns + 2 < self.master.grid.num_columns:
            self.addnotationsAllowed = True
            self.addnotationsMenu = self.master.add_Adnotation_menu('Notes', row = 0, column = min_columns, row_span = 5, column_span = self.master.grid.num_columns - min_columns)
            self.textDisplayer.add_key_command(pycui.keys.KEY_A_LOWER, self.add_adnotation)
            self.textDisplayer.addnotationDisplayer = self.addnotationsMenu
            self.addnotationsMenu.Displayer = self.textDisplayer
            self.addnotationsMenu.add_key_command(pycui.keys.KEY_ENTER, self.handle_adnotation_menu_enter)
            self.textDisplayer.load_adnotations()
        else:
            self.addnotationsAllowed = False
        self.textDisplayer.add_key_command(pycui.keys.KEY_T_LOWER, self.showTOC)
        self.master.run_on_exit(self.exit)
        self.master.move_focus(self.textDisplayer)
    def showTOC(self):
        # show table of contents
        tocList = [k for k, v in self.textDisplayer.getTOC().items()]
        self.master.show_menu_popup('Table of contents', tocList, self.handleTOC)
    def handleTOC(self, arg):
        # select from table of converts
        self.textDisplayer.force_chapter(arg)
        self.master.move_focus(self.textDisplayer)
    def add_adnotation(self):
        # show popup for adnotations
        self.master.show_text_box_popup('Text for adnotation:', self.adnotation_handle)
    def adnotation_handle(self, arg):
        # add adnotation after popup
        self.textDisplayer.add_adnotation_on_cursor(arg)
        self.master.move_focus(self.textDisplayer)
    def exit(self):
        self.textDisplayer.book.dump_to_config(self.textDisplayer.cursor_text_pos_x, self.textDisplayer.cursor_text_pos_y)
    def handle_adnotation_menu_enter(self):
        # jump to selected addnotation
        self.addnotationsMenu.handle_adnotation()
        self.master.move_focus(self.textDisplayer)

def main():
    global config
    # set default path for config
    configPath = os.path.expanduser('~/.tinypub.json')
    parser = argparse.ArgumentParser(description = 'A simple ebook reader with console interface by Grzegorz Koperwas', prog = 'tinyPub', epilog = 'Configuration and reading progress is stored in ~/.tinypub.json', allow_abbrev = True)
    parser.add_argument('file', type = str, help = 'Path to .epub file.', metavar = 'file_path')
    parser.add_argument('--config', dest='config', type = str, help = 'Path to alternative config file', default = configPath, metavar = 'PATH')
    parser.add_argument('--version', action='version', version = __version__)
    args = parser.parse_args()
    # read config, on failure, assume defaults
    try:
        with open(args.config) as f:
            config = json.loads(f.read())
    except FileNotFoundError as e:
        config = {
            'name': 'tinypub v.2',
            'books': {},
            'lineLength': 78,
            'keybinds': {
                'h': 'prev',
                'j': 'down',
                'k': 'up',
                'l': 'next'
            }
        }
    # load ebook
    book = Book(args.file)
    # start ui initialization
    root = impPYCUI(5, 30)
    # show error if terminal is to small
    try:
        s = Interface(root, book)
        root.start()
    except pycui.errors.PyCUIOutOfBoundsError:
        print('Your terminal is too small, try decreasing lineLength in ~/.tinypub.json')
        input()
    # After exit write to config file
    with open(args.config, 'w+') as f:
        f.write(json.dumps(config, indent = 4))

config = None
if __name__ == '__main__':
    main()

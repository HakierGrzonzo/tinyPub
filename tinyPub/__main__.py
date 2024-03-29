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
from .addnotation import Addnotation, Adnotation_menu

__version__ = '2.0.1'
# Debug functions
log = list()

def pp(arg):
    print(json.dumps(arg, indent = 4))


class impPYCUI(pycui.PyCUI):
    """py_cui.PyCUI but with add methods for my classes"""
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


class Displayer(pycui.widgets.ScrollTextBlock):
    """basicly py_cui Text_block that is read only and has some glue for Book()"""
    def __init__(self, id, title, grid, row, column, row_span, column_span, padx, pady, book):
        global config
        self.book = book
        # set title according to book's chapter title
        text, self.breaks, self.org_title = self.book.chapter_returner()
        # pass all parameters and chapter's text to parent class
        super(Displayer, self).__init__(id, self.org_title, grid, row, column, row_span, column_span, padx, pady, text)
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
        self.append_progress_to_title()

    def insert_char(self, key_pressed):
        """hijack insert_char to handle some keybindings"""
        action = self.keybinds.get(chr(key_pressed))
        if action == 'prev':
            # switch chapter to previous one
            text, self.breaks, self.org_title = self.book.select_prev_chapter()
            self.set_text(text)
            self.load_adnotations()
            self.append_progress_to_title()
        if action == 'next':
            # switch chapter to next one
            text, self.breaks, self.org_title = self.book.select_next_chapter()
            self.set_text(text)
            self.load_adnotations()
            self.append_progress_to_title()
        # jump to paragraph break
        if action == 'down':
            for x in self.breaks:
                if x > self.cursor_text_pos_y:
                    self.jump_to_line(x)
                    break
            self.append_progress_to_title()
        if action == 'up':
            for x in self.breaks[::-1]:
                if x < self.cursor_text_pos_y:
                    self.jump_to_line(x)
                    break
            self.append_progress_to_title()

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
            text, self.breaks, self.org_title = self.book.select_chapter(num)
            self.set_text(text)
            self.load_adnotations()
            self.append_progress_to_title()
        except Exception as e:
            global log
            log.append('force_chapter: ' + str(e))

    def append_progress_to_title(self):
        self.title = self.org_title + ' '+ str(max(round(100*self.cursor_text_pos_y / len(self.text_lines)), 0)) + '%'

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

    def move_up(self):
        super().move_up()
        self.append_progress_to_title()

    def move_down(self):
        super().move_down()
        self.append_progress_to_title


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
        # process styles
        styles = dict()
        for x in self.book.get_items_of_type(ebooklib.ITEM_STYLE):
            styles[x.file_name] = StyleHandler(x.get_content())
        # read spine
        spine_ids = [x[0] for x in self.book.spine]
        chapters = list()
        # make dict href → id
        self.id_to_href = dict()
        for item in self.book.get_items():
            self.id_to_href[item.get_id()] = item.get_name()
        for id in spine_ids:
            doc = self.book.get_item_with_id(id)
            chapter = Chapter(doc.content,
                ['sup'],
                lineLength = config.get('lineLength', 78),
                css_data = styles,
                force_justify_on_p_tags= config.get('force_justify_on_p_tags', False)
                )
            chapters.append((chapter, id))
        # get toc
        self.chapters = list()
        try:
            navigation = list(self.book.get_items_of_type(ebooklib.ITEM_NAVIGATION))[0]
            self.navigation = parse_navigation(navigation.content)
            self.navigation.sort(key= lambda item: item["playOrder"])
            href_to_title = dict()
            for item in self.navigation:
                href_to_title[item['content']] = item['title']
            for chapter in chapters:
                item = {
                    'chapter' : chapter[0],
                    'title' : href_to_title.get(self.id_to_href[chapter[1]], chapter[0].title())
                }
                self.chapters.append(item)
        except Exception as e:
            raise e
            for chapter in chapters:
                x = {
                    'chapter' : chapter[0],
                    'title': chapter[0].title()
                }
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
        return text, breaks, str(self.chapters[self.chapterIndex]['title']) + ' ({}/{})'.format(self.chapterIndex + 1, len(self.chapters))

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
        # select from table of contents
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
    parser.add_argument('--cat', const=True, default=False, action="store_const")
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
            },
            'force_justify_on_p_tags': False
        }
    # load ebook
    book = Book(args.file)
    # if --cat → print epub
    if args.cat:
        for chapter in book.chapters:
            text, _ = chapter["chapter"].text()
            print(text)


    else:
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
        print('done!')


config = None
if __name__ == '__main__':
    main()

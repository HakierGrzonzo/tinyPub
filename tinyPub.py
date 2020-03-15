#!/usr/bin/env python
from htmlParser import Chapter
import py_cui as pycui
from ebooklib import epub
import json, os, ebooklib, argparse
from multiprocessing import Pool, cpu_count
from navParser import parse_navigation

log = list()

def pp(arg):
    print(json.dumps(arg, indent = 4))

class impPYCUI(pycui.PyCUI):
    def __init__(self, arg1, arg2):
        super(impPYCUI, self).__init__(arg1, arg2)
    def add_Displayer(self, title, row, column, row_span = 1, column_span = 1, padx = 1, pady = 0, book = None):
        id = 'Widget{}'.format(len(self.widgets.keys()))
        new_displayer = Displayer(id, title,  self.grid, row, column, row_span, column_span, padx, pady, book)
        self.widgets[id] = new_displayer
        if self.selected_widget is None:
            self.set_selected_widget(id)
        return new_displayer

class Displayer(pycui.widgets.ScrollTextBlock):
    """ basicly py_cui Text_block that is read only"""
    def __init__(self, id, title, grid, row, column, row_span, column_span, padx, pady, book):
        global config
        self.book = book
        text, self.breaks = self.book.chapter_returner()
        super(Displayer, self).__init__(id, title, grid, row, column, row_span, column_span, padx, pady, text)
        self.keybinds = config.get('keybindings', {'h': 'prev', 'j': 'down', 'k': 'up', 'l': 'next'})
        last = None
        while self.cursor_text_pos_y < self.book.XcursorPos:
            last = self.cursor_text_pos_y
            self.move_down()
            if last == self.cursor_text_pos_y:
                break
        while self.cursor_text_pos_x < self.book.YcursorPos:
            last = self.cursor_text_pos_x
            self.move_right()
            if last == self.cursor_text_pos_x:
                break
    def insert_char(self, key_pressed):
        """hijack insert_char to handle keybindings"""
        action = self.keybinds.get(chr(key_pressed))
        if action == 'prev':
            text, self.breaks = self.book.select_prev_chapter()
            self.set_text(text)
        if action == 'next':
            text, self.breaks = self.book.select_next_chapter()
            self.set_text(text)
        if action == 'down':
            for x in self.breaks:
                if x > self.cursor_text_pos_y:
                    last = self.cursor_text_pos_y
                    while self.cursor_text_pos_y < x:
                        last = self.cursor_text_pos_y
                        self.move_down()
                        if last == self.cursor_text_pos_y:
                            break
                    break
        if action == 'up':
            for x in self.breaks[::-1]:
                if x < self.cursor_text_pos_y:
                    last = self.cursor_text_pos_y
                    while x < self.cursor_text_pos_y:
                        last = self.cursor_text_pos_y
                        self.move_up()
                        if last == self.cursor_text_pos_y:
                            break
                    break
    def handle_delete(self):
        pass
    def handle_backspace(self):
        pass
    def handle_newline(self):
        pass
    def getTOC(self):
        res = dict()
        i = 1
        for item in self.book.chapters:
            res[str(i) + '. ' + item['title']] = i
            i += 1
        return res
    def force_chapter(self, identifier):
        try:
            num = self.getTOC()[identifier] - 1
            text, self.breaks = self.book.select_chapter(num)
            self.set_text(text)
        except Exception as e:
            global log
            log.append('force_chapter: ' + str(e))

class Book(object):
    """docstring for Book."""
    def __init__(self, pathToFile):
        global config
        super(Book, self).__init__()
        try:
            self.book = epub.read_epub(pathToFile)
        except Exception as e:
            raise ValueError('Exception while importing epub:', str(e))
        chapters = dict()
        for item in self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            chapter = Chapter(item.content, ['sup'], lineLength = config.get('lineLength', 78))
            if chapter.hasBody:
                chapters[item.file_name] = chapter
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
        except Exception as e:
            self.chapters = list()
            for chapter in chapters:
                x = dict()
                x['chapter'] = chapter
                self.chapters.append(x)
        self.configEntry = config.get('books').get(self.title(), dict())
        self.chapterIndex = self.configEntry.get('chapter', 1)
        self.XcursorPos = self.configEntry.get('cursorX', 0)
        self.YcursorPos = self.configEntry.get('cursorY', 0)
        self.addnotations = self.configEntry.get('addnotations', dict()).get(self.chapterIndex, list())
    def chapter_returner(self):
        text, breaks = self.chapters[self.chapterIndex]['chapter'].text()
        # TODO: add addnotations insertion
        return text, breaks
    def title(self):
        return self.book.get_metadata('DC', 'title')[0][0]
    def select_chapter(self, new_chapter_num):
        if new_chapter_num < 0 or new_chapter_num > len(self.chapters) - 1:
            raise ValueError('Chapter does not exist')
        try:
            self.configEntry['addnotations'][self.chapterIndex] = self.addnotations
        except:
            self.configEntry['addnotations'] = dict()
            self.configEntry['addnotations'][self.chapterIndex] = self.addnotations
        self.chapterIndex = new_chapter_num
        self.XcursorPos = 0
        self.YcursorPos = 0
        self.addnotations = self.configEntry.get('addnotations').get(self.chapterIndex, list())
        return self.chapter_returner()
    def select_next_chapter(self):
        try:
            return self.select_chapter(self.chapterIndex + 1)
        except Exception as e:
            return self.chapter_returner()
    def select_prev_chapter(self):
        try:
            return self.select_chapter(self.chapterIndex - 1)
        except Exception as e:
            return self.chapter_returner()
    def dump_to_config(self, YcursorPos, XcursorPos):
        global config
        self.configEntry = {
            'chapter': self.chapterIndex,
            'cursorX': XcursorPos,
            'cursorY': YcursorPos,
            'addnotations': self.configEntry.get('addnotations', dict())
        }
        config['books'][self.title()] = self.configEntry

class Interface:
    def __init__(self, master, book):
        self.master = master
        self.book = book
        master.toggle_unicode_borders()
        # calculate width for given lineLength
        lineLength = config.get('lineLength', 78)
        min_columns = (lineLength + 5) // self.master.grid.column_width + 1
        self.textDisplayer = self.master.add_Displayer(self.book.title(), row = 0, column = 0, row_span = 5, column_span = min_columns, book = self.book)
        self.textDisplayer.add_key_command(pycui.keys.KEY_T_LOWER, self.showTOC)
        self.master.run_on_exit(self.exit)
    def showTOC(self):
        tocList = [k for k, v in self.textDisplayer.getTOC().items()]
        self.master.show_menu_popup('Table of contents', tocList, self.textDisplayer.force_chapter)
    def exit(self):
        self.textDisplayer.book.dump_to_config(self.textDisplayer.cursor_text_pos_x, self.textDisplayer.cursor_text_pos_y)


if __name__ == '__main__':
    configPath = os.path.expanduser('~/.tinypub.json')
    parser = argparse.ArgumentParser(description = 'A crude epub reader.')
    parser.add_argument('file', type = str, help = 'Path to .epub file.', metavar = 'file_path')
    parser.add_argument('--config', dest='config', type = str, help = 'Path to alternative config file', default = configPath, metavar = 'path')
    args = parser.parse_args()
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
    book = Book(args.file)
    root = impPYCUI(5, 10)
    root.set_title = 'tinypub test'
    s = Interface(root, book)
    root.start()
    # After exit
    with open(args.config, 'w+') as f:
        f.write(json.dumps(config, indent = 4))

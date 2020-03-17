#!/usr/bin/env python
from htmlParser import Chapter
import py_cui as pycui
from ebooklib import epub
import json, os, ebooklib, argparse
from multiprocessing import Pool, cpu_count
from navParser import parse_navigation

log = list()
def shortText(text, limit):
        """shorten text to limit"""
        if len(text) > limit + 4 and limit > 4:
                text = text[:limit] + '...'
        return text

def pp(arg):
    print(json.dumps(arg, indent = 4))

class Addnotation():
    """docstring for addnotation."""
    def __init__(self, breaks, text = str(), position = -1, dict = dict()):
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
        return self.breaks[self.pos]
    def dump(self):
        return {'position': self.pos, 'text': self.text}


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
    def add_Adnotation_menu(self, title, row, column, row_span = 1, column_span = 1, padx = 1, pady = 0):
        id = 'Widget{}'.format(len(self.widgets.keys()))
        new_adnotation_menu = Adnotation_menu(id, title, self.grid, row, column, row_span, column_span, padx, pady)
        self.widgets[id] = new_adnotation_menu
        if self.selected_widget is None:
            self.set_selected_widget(id)
        return new_adnotation_menu

class Adnotation_menu(pycui.widgets.ScrollMenu):
    def __init__(self, id, title, grid, row, column, row_span, column_span, padx, pady):
        super(Adnotation_menu, self).__init__(id, title, grid, row, column, row_span, column_span, padx, pady)
        self.decoding_dict = dict()
        self.Displayer = None
    def add_adnotation(self, adnotation):
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
        adnotation = self.decoding_dict[self.get()]
        self.Displayer.jump_to_line(adnotation.raw_pos())



class Displayer(pycui.widgets.ScrollTextBlock):
    """ basicly py_cui Text_block that is read only"""
    def __init__(self, id, title, grid, row, column, row_span, column_span, padx, pady, book):
        global config
        self.book = book
        text, self.breaks, self.title = self.book.chapter_returner()
        super(Displayer, self).__init__(id, self.title, grid, row, column, row_span, column_span, padx, pady, text)
        self.keybinds = config.get('keybindings', {'h': 'prev', 'j': 'down', 'k': 'up', 'l': 'next'})
        last = None
        self.addnotationDisplayer = None
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
            text, self.breaks, self.title = self.book.select_prev_chapter()
            self.set_text(text)
            self.load_adnotations()
        if action == 'next':
            text, self.breaks, self.title = self.book.select_next_chapter()
            self.set_text(text)
            self.load_adnotations()
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
        self.addnotationDisplayer.clear()
        for x in self.book.addnotations:
            self.addnotationDisplayer.add_adnotation(x)
    def add_adnotation_on_cursor(self, text):
        adnotation = self.book.add_adnotation(text, self.cursor_text_pos_y, self.breaks)
        self.addnotationDisplayer.add_adnotation(adnotation)
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
            text, self.breaks, self.title = self.book.select_chapter(num)
            self.set_text(text)
            self.load_adnotations()
        except Exception as e:
            global log
            log.append('force_chapter: ' + str(e))
    def jump_to_line(self, line):
        if self.cursor_text_pos_y > line:
            last = self.cursor_text_pos_y
            while line < self.cursor_text_pos_y:
                last = self.cursor_text_pos_y
                self.move_up()
                if last == self.cursor_text_pos_y:
                    break
        elif self.cursor_text_pos_y < line:
            last = self.cursor_text_pos_y
            while self.cursor_text_pos_y < line:
                last = self.cursor_text_pos_y
                self.move_down()
                if last == self.cursor_text_pos_y:
                    break

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
        self.chapterIndex = int(self.configEntry.get('chapter', 1))
        self.XcursorPos = self.configEntry.get('cursorX', 0)
        self.YcursorPos = self.configEntry.get('cursorY', 0)
    def chapter_returner(self):
        text, breaks = self.chapters[self.chapterIndex]['chapter'].text()
        addnotations = self.configEntry.get('addnotations', dict()).get(str(self.chapterIndex), list())
        self.addnotations = [Addnotation(breaks, dict = x) for x in addnotations]
        return text, breaks, self.chapters[self.chapterIndex]['title']
    def title(self):
        return self.book.get_metadata('DC', 'title')[0][0]
    def select_chapter(self, new_chapter_num):
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
        try:
            return self.select_chapter(self.chapterIndex + 1)
        except Exception as e:
            return self.chapter_returner()
    def select_prev_chapter(self):
        try:
            return self.select_chapter(self.chapterIndex - 1)
        except Exception as e:
            return self.chapter_returner()
    def add_adnotation(self, text, y_pos, breaks):
        res = Addnotation(breaks, text = text, position = y_pos)
        self.addnotations.append(res)
        return res
    def dump_to_config(self, YcursorPos, XcursorPos):
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
    def __init__(self, master, book):
        self.master = master
        self.book = book
        self.master.toggle_unicode_borders()
        self.master.set_title(self.book.title())
        self.master.grid.offset_x = 0
        self.master.grid.offset_y = 0
        # calculate width for given lineLength
        lineLength = config.get('lineLength', 78)
        min_columns = (lineLength + 15) // self.master.grid.column_width + 1
        try:
            self.textDisplayer = self.master.add_Displayer('' ,row = 0, column = 0, row_span = 5, column_span = min_columns, book = self.book)
        except:
            self.textDisplayer = self.master.add_Displayer('' ,row = 0, column = 0, row_span = 5, column_span = self.master.grid.num_columns, book = self.book)
        if min_columns + 2 < self.master.grid.num_columns:
            self.addnotationsAllowed = True
            self.addnotationsMenu = self.master.add_Adnotation_menu('Adnotations', row = 0, column = min_columns, row_span = 5, column_span = self.master.grid.num_columns - min_columns)
            self.textDisplayer.add_key_command(pycui.keys.KEY_A_LOWER, self.add_adnotation)
            self.textDisplayer.addnotationDisplayer = self.addnotationsMenu
            self.addnotationsMenu.Displayer = self.textDisplayer
            self.addnotationsMenu.add_key_command(pycui.keys.KEY_ENTER, self.addnotationsMenu.handle_adnotation)
            self.textDisplayer.load_adnotations()
        else:
            self.addnotationsAllowed = False
        self.textDisplayer.add_key_command(pycui.keys.KEY_T_LOWER, self.showTOC)
        self.master.run_on_exit(self.exit)
    def showTOC(self):
        tocList = [k for k, v in self.textDisplayer.getTOC().items()]
        self.master.show_menu_popup('Table of contents', tocList, self.textDisplayer.force_chapter)
    def add_adnotation(self):
        self.master.show_text_box_popup('Text for adnotation:', self.textDisplayer.add_adnotation_on_cursor)
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
    root = impPYCUI(5, 30)
    try:
        s = Interface(root, book)
        root.start()
    except pycui.errors.PyCUIOutOfBoundsError:
        print('Your terminal is too small, try decreasing lineLength in ~/.tinypub.json')
        input()
    # After exit
    with open(args.config, 'w+') as f:
        f.write(json.dumps(config, indent = 4))

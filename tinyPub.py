#!/usr/bin/env python
from ebooklib import epub
import fileinput, json
import ebooklib
import os, sys
import prompt_toolkit as pt
import html2text
from prompt_toolkit import Application
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.buffer import  Buffer

__version__ = 'tinypub v.1'
log = list()
html2text.BODY_WIDTH = 90

def CleanUpper(text):
    global log 
    res = str() 
    for line in text:
        try:
            textToStrip = line[line.find('](') + 1: line.find(')') + 1]
            if line.find('](') != -1:
                line = line.replace(textToStrip, '')
                line = line.replace('![','')
                #line = line.replace('[','').replace(']','')
            else:
                line = line.replace(textToStrip, '')
                line = line.replace('![','')
            log.append('Striping:' + textToStrip)
        except Exception as e:
            log.append(e) 
        if line != str():
            res += line + ' '
        else:
            res += '\n'
    return html2text.optwrap(res).split('\n')


def OpenChapter(chapter, images = None):
    text = chapter.get_body_content().decode("utf-8")
    text = html2text.html2text(text)
    text = text.split('\n')
    text = CleanUpper(text)
    res = str()
    breaks = list()
    for line in text:
        res += ' '  + line + '\n'
        if line == str():
            breaks.append(len(res) - 2)
    return res, breaks

def OpenFile(file):
    book = epub.read_epub(file)
    chapters = list()
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            chapters.append(item)
    return chapters, book.get_metadata('DC', 'title')

def SetState(state_):
    global state
    state = state_

def Display(text, cursorPos = 0, titlebar = str(), breaks = None):
    kb = KeyBindings()
    try:
        doc = pt.document.Document(text = text, cursor_position = cursorPos)
    except AssertionError:
        doc = pt.document.Document(text = text, cursor_position = 0)
    Displayer = Buffer(read_only = True, multiline = True, document = doc)
    SetState(None)
    @kb.add('j')
    def parNext_(event):
        if not breaks == None:
            for par in breaks:
                if par > Displayer.cursor_position:
                    Displayer._set_cursor_position(par)
                    break
    @kb.add('k')
    def parPrev_(event):
        if not breaks == None:
            x = breaks.copy()
            x.reverse()
            for par in x:
                if par < Displayer.cursor_position:
                    Displayer._set_cursor_position(par)
                    break

    @kb.add('c-q')
    def exit_(event):
        SetState('exit')
        event.app.exit()

    @kb.add('l')
    def next_(event):
        SetState('next')
        event.app.exit()

    @kb.add('h')
    def prev_(event):
        SetState('prev')
        event.app.exit()

    Tooltip = pt.HTML('<ansigreen>Press crtl-q to exit ' + titlebar + ' </ansigreen>')
    root_container = HSplit([
        Window(content = BufferControl(buffer = Displayer)),
        Window(content = FormattedTextControl(text = Tooltip))
        ])

    layout = Layout(root_container)
    app = Application(key_bindings = kb, layout = layout, full_screen = True)
    app.run()
    return Displayer.cursor_position

def Settings():
    global __version__
    try:
        file = open(os.path.expanduser('~/.tinypub.json'), 'r')
        settings = json.loads(file.read())
    except:
        file = open(os.path.expanduser('~/.tinypub.json'), 'w+')
        file.write(json.dumps({'name': __version__}))
        file.close()
        file = open(os.path.expanduser('~/.tinypub.json'), 'r')
        settings = json.loads(file.read())
    # Convert old .tinypub.json formats to new spec
    if not 'books' in settings.keys():
        settings['books'] = dict()
        for key, value in settings.items():
            if key != 'name' and key != 'books':
                settings['books'][key] = value
        settings['name'] = __version__
    return settings

def DumpSettings(settings):
    file = open(os.path.expanduser('~/.tinypub.json'), 'w')
    file.write(json.dumps(settings))

def main(fname):
    global settings
    global state
    book, bookTitle = OpenFile(fname)
    bookTitle, x = bookTitle[0]
    try:
        chapter = settings['books'][bookTitle]['chapter']
        cursor = settings['books'][bookTitle]['cursor']
    except:
        settings['books'][bookTitle] = dict()
        chapter = 0
        cursor = 0
        settings['books'][bookTitle]['pathToFile'] = fname
    if chapter >= len(book):
        chapter = 0
        cursor = 0
        input('The saved stats were corrupted, starting from first chapter. Press any key to continue.')
    while state != 'exit':
        try:
            status = ' ' + str(chapter + 1) + '/' + str(len(book))
            text, breaks = OpenChapter(book[chapter])
            cursor = Display(text, cursorPos = cursor, titlebar = status, breaks=breaks)
            if state == 'next':
                cursor = 0
                chapter += 1
                if chapter == len(book):
                    state = 'exit'
                    print('The End')
            elif state == 'prev':
                cursor = 0
                if not chapter == 0:
                    chapter -= 1
        except Exception as e:
            print(e)
            raise e
            SetState('exit')
    settings['books'][bookTitle]['chapter'] = chapter
    settings['books'][bookTitle]['cursor'] = cursor
    DumpSettings(settings)

if __name__ == '__main__':
    Debug = False 
    state = None
    settings = Settings()
    if len(sys.argv) > 1:
        fname = str()
        for x in sys.argv[1:]:
            fname += x + ' '
        fname = fname[:len(fname) - 1]
        main(fname)
    else:
        raise Exception('File not specified')
    if Debug:
        for x in log:
            print(x)

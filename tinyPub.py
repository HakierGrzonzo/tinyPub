#!/usr/bin/env python
from ebooklib import epub
import fileinput, json
import ebooklib
import os, sys
import prompt_toolkit as pt
from htmlParser import Chapter
from multiprocessing import pool, cpu_count

__version__ = 'tinypub v.1'
log = list()


def proccesChapter(item):
    return Chapter(item.get_body_content(), ignored_tags_ = ['sup']).text()

def OpenFile(fname):
    book = epub.read_epub(fname)
    p = pool.Pool(cpu_count())
    res = p.map(proccesChapter ,list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT)))
    result = list()
    for x in res:
        if not x == None:
            result.append(x)
    return result, book.get_metadata('DC', 'title')

def Settings():
    global __version__
    try:
        file = open(os.path.expanduser('~/.tinypub.json'), 'r')
        settings = json.loads(file.read())
        file.close()
    except:
        file = open(os.path.expanduser('~/.tinypub.json'), 'w+')
        file.write(json.dumps({'name': __version__}))
        file.close()
        file = open(os.path.expanduser('~/.tinypub.json'), 'r')
        settings = json.loads(file.read())
        file.close()
    # Convert old .tinypub.json formats to new spec
    if not 'books' in settings.keys():
        settings['books'] = dict()
        for key, value in settings.items():
            if key != 'name' and key != 'books':
                settings['books'][key] = value
        settings['name'] = __version__
    return settings


def Display(book, chapter = 0, cursor = 0):

    def makeDocument(chapter, cursor = 0):
        text, breaks =  chapter
        try:
            return pt.document.Document(text = text, cursor_position = cursor), breaks
        except:
            return pt.document.Document(text = text, cursor_position = 0), breaks

    def GetBottomText(doc = None):
        nonlocal chapter, book
        text = str(chapter + 1) +'/'+ str(len(book))
        if not doc == None:
            percentage = int((doc.cursor_position + 2) / len(doc.text) * 100)
            text += ' ' + str(percentage) + '% '
        if chapter + 1 == len(book):
            text += 'The end :('
        return pt.document.Document(text = text)

    doc, breaks = makeDocument(book[chapter], cursor)
    disp = pt.layout.controls.BufferControl( pt.buffer.Buffer(document = doc, read_only = True))
    kb = pt.key_binding.KeyBindings()
    dynamicBuffer = pt.buffer.Buffer(document = GetBottomText(doc), read_only = True, multiline = False, name = 'status')
    dynamic = pt.layout.controls.BufferControl(buffer = dynamicBuffer, focusable = False)

    def updateBottomText(event):
        try:
            dynamicBuffer = event.app.layout.get_buffer_by_name('status')
            dynamicBuffer.set_document(GetBottomText(event.app.current_buffer.document), bypass_readonly = True)
        except:
            dynamicBuffer = event.layout.get_buffer_by_name('status')
            dynamicBuffer.set_document(GetBottomText(event.current_buffer.document), bypass_readonly = True)

    @kb.add('c-q')
    def exit_(event):
        nonlocal cursor
        cursor = event.app.current_buffer.cursor_position
        event.app.exit()

    @kb.add('j')
    def parNext_(event):
        try:
            if not breaks == None:
                Displayer = event.app.current_buffer
                for par in breaks:
                    if par > Displayer.cursor_position:
                        Displayer._set_cursor_position(par)
                        break
        except:
            pass
    @kb.add('k')
    def parPrev_(event):
        try:
            if not breaks == None:
                Displayer = event.app.current_buffer
                x = breaks.copy()
                x.reverse()
                for par in x:
                    if par < Displayer.cursor_position:
                        Displayer._set_cursor_position(par)
                        break
        except:
            pass
    @kb.add('h')
    def prev_(event):
        nonlocal chapter, breaks
        if chapter > 0:
            chapter -= 1
            doc, breaks = makeDocument(book[chapter])
            event.app.current_buffer.set_document(doc, bypass_readonly = True)

    @kb.add('l')
    def prev_(event):
        nonlocal chapter, breaks
        if chapter < len(book)-1:
            chapter += 1
            doc, breaks = makeDocument(book[chapter])
            event.app.current_buffer.set_document(doc, bypass_readonly = True)

    Tooltip = pt.layout.controls.FormattedTextControl(text =
            pt.HTML('<ansigreen>Press crtl-q to exit </ansigreen>'))
    container = pt.layout.Layout(pt.layout.containers.HSplit([
        pt.layout.containers.Window(content = disp),
        pt.layout.containers.VSplit([
            pt.layout.containers.Window(content = Tooltip, dont_extend_width = True),
            pt.layout.containers.Window(content = dynamic)
            ])
        ]))
    app = pt.Application(key_bindings = kb, layout = container, full_screen = True, on_invalidate = updateBottomText)
    app.run()

    return chapter, cursor

def DumpSettings(settings):
    file = open(os.path.expanduser('~/.tinypub.json'), 'w')
    file.write(json.dumps(settings))
    file.close()

def main(fname):
    global settings
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
    chapter, cursor = Display(book, chapter, cursor)
    settings['books'][bookTitle]['chapter'] = chapter
    settings['books'][bookTitle]['cursor'] = cursor
    DumpSettings(settings)

if __name__ == '__main__':
    Debug = True
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

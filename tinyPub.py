#!/usr/bin/env python
from htmlParser import Chapter
import prompt_toolkit as pt
from ebooklib import epub
import json, os, ebooklib, argparse
from multiprocessing import Pool, cpu_count
from navParser import parse_navigation

def pp(arg):
    print(json.dumps(arg, indent = 4))

class Book(object):
    """docstring for Book."""
    def __init__(self, pathToFile):
        super(Book, self).__init__()
        try:
            self.book = epub.read_epub(pathToFile)
        except Exception as e:
            raise ValueError('Exception while importing epub:', str(e))
        chapters = dict()
        for item in self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            chapter = Chapter(item.content, ['sup'])
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
            print(self.chapters)
        except Exception as e:
            self.chapters = list()
            for chapter in chapters:
                x = dict()
                x['chapter'] = chapter
                self.chapters.append(x)
    def title(self):
        return self.book.get_metadata('DC', 'title')[0][0]



if __name__ == '__main__':
    configPath = os.path.expanduser('~/.tinypub.json')
    parser = argparse.ArgumentParser(description = 'A crude epub reader.')
    parser.add_argument('file', type = str, help = 'Path to .epub file.', metavar = 'file_path')
    parser.add_argument('--config', dest='config', type = str, help = 'Path to alternative config file', default = configPath, metavar = 'path')
    args = parser.parse_args()
    configFile = open(args.config)
    config = json.loads(configFile.read())
    Book(args.file)

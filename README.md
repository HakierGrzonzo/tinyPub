# tinyPub.py

![This thing in action](https://i.imgur.com/Bfxw5KS.png)

A simple, [py_cui](https://github.com/jwlodek/py_cui) based, terminal ebook reader for .epub files.

```
pip install tinypub-HakierGrzonzo
```
and then you should be able to use it with:
```
tinypub <path to file>
```

Features:

- Your cursor should be exactly where you left it, as your progress is tracked in ~/.tinypub.json file
- You can create short notes, and quickly jump to them.
- Somewhat scalable interface. I mean, it works on startup…

## How to use:

Run it with your ebook's epub file as an artgument.

On the bottom of your screen you will see help messages.

You can use cursor keys to move the cursor, you can use "k" and "j" keys to jump to next paragraph break.

You can use "h" and "l" keys to switch between chapters.

Pressing "t" opens up Table of Contents.

Pressing "a" allows you to add a note at cursor.

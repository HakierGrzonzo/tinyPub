# tinyPub.py

A crude, prompt_toolkit based, python *.epub* reader.

It keeps track of your reading progress in a .tinyPub.json file in your home directory.

## How to use:

Just run it with your *.epub* file as an argument:

```
./tinyPub.py <path to ebook>
```

It works on linux, maybe works on windows.

### Keybindings:

|   h    | previous chapter                      |
| :----: | ------------------------------------- |
|   l    | next chapter                          |
|   j    | move cursor to the previous paragraph |
|   k    | move the cursor to the next paragraph |
| arrows | move the cursor                       |
| crtl-q | quit tinyPub (and save progress)      |


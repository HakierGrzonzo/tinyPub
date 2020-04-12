import py_cui as pycui
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

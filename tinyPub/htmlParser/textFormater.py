normal_text = u'qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'
# bold_text = u'𝗾𝘄𝗲𝗿𝘁𝘆𝘂𝗶𝗼𝗽𝗮𝘀𝗱𝗳𝗴𝗵𝗷𝗸𝗹𝘇𝘅𝗰𝘃𝗯𝗻𝗺𝗤𝗪𝗘𝗥𝗧𝗬𝗨𝗜𝗢𝗣𝗔𝗦𝗗𝗙𝗚𝗛𝗝𝗞𝗟𝗭𝗫𝗖𝗩𝗕𝗡𝗠'
bold_text = u'𝚚𝚠𝚎𝚛𝚝𝚢𝚞𝚒𝚘𝚙𝚊𝚜𝚍𝚏𝚐𝚑𝚓𝚔𝚕𝚣𝚡𝚌𝚟𝚋𝚗𝚖𝚀𝚆𝙴𝚁𝚃𝚈𝚄𝙸𝙾𝙿𝙰𝚂𝙳𝙵𝙶𝙷𝙹𝙺𝙻𝚉𝚇𝙲𝚅𝙱𝙽𝙼'
italic_text = u'𝘲𝘸𝘦𝘳𝘵𝘺𝘶𝘪𝘰𝘱𝘢𝘴𝘥𝘧𝘨𝘩𝘫𝘬𝘭𝘻𝘹𝘤𝘷𝘣𝘯𝘮𝘘𝘞𝘌𝘙𝘛𝘠𝘜𝘐𝘖𝘗𝘈𝘚𝘋𝘍𝘎𝘏𝘑𝘒𝘓𝘡𝘟𝘊𝘝𝘉𝘕𝘔'
bold_italic_text = u'𝙦𝙬𝙚𝙧𝙩𝙮𝙪𝙞𝙤𝙥𝙖𝙨𝙙𝙛𝙜𝙝𝙟𝙠𝙡𝙯𝙭𝙘𝙫𝙗𝙣𝙢𝙌𝙒𝙀𝙍𝙏𝙔𝙐𝙄𝙊𝙋𝘼𝙎𝘿𝙁𝙂𝙃𝙅𝙆𝙇𝙕𝙓𝘾𝙑𝘽𝙉𝙈'

i = 0
bold_dict = dict()
italic_dict = dict()
bold_italic_dict = dict()
for i in range(len(normal_text)):
    bold_dict[normal_text[i]] = bold_text[i]
    bold_dict[italic_text[i]] = bold_italic_text[i]
    italic_dict[normal_text[i]] = italic_text[i]
    italic_dict[bold_text[i]] = bold_italic_text[i]
    bold_italic_dict[normal_text[i]] = bold_italic_text[i]
    bold_italic_dict[bold_text[i]] = bold_italic_text[i]
    bold_italic_dict[italic_text[i]] = bold_italic_text[i]

def italic(string):
    res = str()
    for char in string:
        res += italic_dict.get(char, char)
    return res

def bold(string):
    res = str()
    for char in string:
        res += bold_dict.get(char, char)
    return res

def bolditalic(string):
    res = str()
    for char in string:
        res += bold_italic_dict.get(char, char)
    return res

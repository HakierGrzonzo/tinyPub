from bs4 import BeautifulSoup as Soup
from urllib.parse import unquote

def parse_navigation(raw):
    soup = Soup(raw.decode('utf-8'), features ='lxml').find('navmap')
    navEntries = list()
    for entry in soup.find_all('navpoint'):
        res = dict()
        res['title'] = entry.find('text').get_text()
        res['playOrder'] = int(entry.get('playorder'))
        res['content'] = unquote(entry.find('content').get('src'))
        navEntries.append(res)
    return sorted(navEntries, key = lambda item: item['playOrder'])

from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup as Soup
from pytz import timezone, UTC

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

URL = 'https://goal.co/'

def goal() -> dict:
    data = []
    match = []
    req = requests.get(URL, headers=headers)
    
    if req.status_code != 200:
        return {'error': 'Failed to fetch data'}

    html = Soup(req.content, 'html.parser')

    tbody_tags = html.find_all('tr')

    for tbody in tbody_tags:

        tb1 = tbody.find('td' , class_='utable_f1 f')
        tb2 = tbody.find('td' , class_='utable_f2 f')
        tb3 = tbody.find('td' , class_='utable_f3 f classodds')
        
        # print(tb)
        if tb1 is not None:
            tb1 = tb1.text.strip()
        if tb2 is not None:
            tb2 = tb2.text.strip()
        if tb3 is not None:
            tb3 = tb3.text.strip()

        if tb1 != None:
            match.append({
                'เวลา': tb1,
                'เจ้าบ้าน': tb2,
                'ราคาบอล': tb3
            })
            
        td = tbody.find('td', class_='utable_league')
        
        if td is not None:
            league_name = td.text.strip()
            
            data.append({
                'league': league_name,
                'matches': match
            })
            
    return data


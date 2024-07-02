import subprocess
from typing import List, Dict, Any
from bs4 import BeautifulSoup as Soup

URL = 'https://goal1.co/'

def fetch_with_curl(url: str) -> str:
    command = [
        'curl',
        '-H', "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        '-s',  # silent mode
        url
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout

def format_string(s: str) -> str:
    return ' '.join(s.replace('\xa0', ' ').split())

def goal(index: int = 0) -> List[Dict[str, Any]]:
    data = []
    
    print(f'Fetching data from Goal1.co (index: {index})')
    html = fetch_with_curl(URL)
    
    soup = Soup(html, 'html.parser')
    
    # Find the todaytable
    today_table = soup.find('div', id='todaytable')
    
    if not today_table:
        print("Could not find the todaytable.")
        return data

    # Find all divs inside todaytable with 'border:1px #000 solid' in their style
    target_divs = today_table.find_all('div', style=lambda value: value and 'border:1px #000 solid' in value)
    
    if not target_divs:
        print("Could not find any div with border style.")
        return data
    
    if index >= len(target_divs):
        print(f"Index {index} is out of range. Only {len(target_divs)} divs found.")
        return data

    target_div = target_divs[index]
    tbody_tags = target_div.find_all('tr')

    current_league = None
    current_matches = []

    for tbody in tbody_tags:
        league_td = tbody.find('td', class_='utable_league')
        if league_td:
            if current_league:
                data.append({
                    'date': format_string(target_div.find('strong').text) if target_div.find('strong') else None,
                    'leagues': current_league,
                    'matches': current_matches
                })
            current_league = format_string(league_td.text)
            current_matches = []
        else:
            match = {}
            for class_name, key in [
                ('utable_f1 f', 'เวลา'),
                ('utable_f2 f', 'เจ้าบ้าน'),
                ('utable_f3 f classodds', 'ราคาบอล'),
                ('utable_f4 f', 'ทีมเยือน'),
                ('utable_f7 f', 'ครึี่งแรก'),
                ('utable_f5 f classmore', 'ผลบอล'),
                ('utable_f6 f', 'ทรรศนะฟุตบอลวันนี้')
            ]:
                td = tbody.find('td', class_=class_name)
                if td:
                    if class_name == 'utable_f4 f':
                        span = td.find('span')
                        match[key] = format_string(span.text if span else td.text)
                    else:
                        match[key] = format_string(td.text)
            if match:
                current_matches.append(match)

    # Add the last league after the loop
    if current_league:
        data.append({
            'date': format_string(target_div.find('strong').text) if target_div.find('strong') else None,
            'leagues': current_league,
            'matches': current_matches
        })
            
    return data

def main():
    # Get data from the first div (index 0)
    result = goal(0)
    print("Data from the first div:")
    for item in result:
        print(f"Date: {item['date']}")
        print(f"League: {item['leagues']}")
        print(f"Number of matches: {len(item['matches'])}")
        print("---")

    # Uncomment the following lines to get data from the second div (index 1)
    # result = goal(1)
    # print("\nData from the second div:")
    # for item in result:
    #     print(f"Date: {item['date']}")
    #     print(f"League: {item['leagues']}")
    #     print(f"Number of matches: {len(item['matches'])}")
    #     print("---")

if __name__ == "__main__":
    main()
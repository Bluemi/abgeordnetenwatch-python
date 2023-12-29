#!/usr/bin/env python3


import json
from pprint import pprint

import requests


def main_api():
    # pprint(politicans.get_politicians(last_name='Gysi'))
    r = requests.get('https://www.abgeordnetenwatch.de/api/v2/topics/2')
    if r.ok:
        with open('data/topic.json', 'w') as f:
            json.dump(r.json(), f, indent=4)


def main_file():
    with open('data/parties.json', 'r') as f:
        data = json.load(f)
    pprint(data['data'][0])


if __name__ == '__main__':
    main_api()
    # main_file()

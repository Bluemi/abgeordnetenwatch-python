#!/usr/bin/env python3


import json
from pprint import pprint

import politicians


def main_api():
    example_politician = politicians.get_politicians(first_name='Eugen', last_name='Schmidt')[0]
    url = example_politician.get_questions_answers_url(0)
    print('url:', url)


def main_file():
    with open('data/parties.json', 'r') as f:
        data = json.load(f)
    pprint(data['data'][0])


if __name__ == '__main__':
    main_api()
    # main_file()

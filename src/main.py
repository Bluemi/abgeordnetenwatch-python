#!/usr/bin/env python3


import json
from pprint import pprint

from bs4 import BeautifulSoup

import politicians
import utils


def save_page():
    example_politician = politicians.get_politicians(first_name='Philipp', last_name='Bruck')[0]
    utils.save_page(example_politician)


def load_page():
    with open('pages/philipp_bruck.html', 'r') as f:
        text = f.read()
    soup = BeautifulSoup(text, 'html.parser')


def main_file():
    with open('data/parties.json', 'r') as f:
        data = json.load(f)
    pprint(data['data'][0])


if __name__ == '__main__':
    save_page()
    # main_file()

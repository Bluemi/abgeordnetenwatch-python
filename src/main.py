#!/usr/bin/env python3


import json
from pprint import pprint

import politicans
from utils import QuestionAnswersParser


def main_api():
    example_politician = politicans.get_politicians(first_name='Heike', last_name='Wermer')[0]
    hrefs = example_politician.get_questions_answers()
    for href in hrefs:
        print(href)


def main_file():
    with open('data/parties.json', 'r') as f:
        data = json.load(f)
    pprint(data['data'][0])


if __name__ == '__main__':
    main_api()
    # main_file()

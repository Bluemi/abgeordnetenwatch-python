#!/usr/bin/env python3


import json
from pprint import pprint

import politicans


def main_api():
    example_politician = politicans.get_politicians(first_name='Björn', last_name='Thümler')[0]
    questions_answers = example_politician.load_questions_answers()

    for question, answer in questions_answers:
        print('Question: ', question)
        print('\nAnswer: ', answer)
        print('#'*60)


def main_file():
    with open('data/parties.json', 'r') as f:
        data = json.load(f)
    pprint(data['data'][0])


if __name__ == '__main__':
    main_api()
    # main_file()

import argparse
import json
import os
import sys

import politicians
from utils import questions_answers_to_csv, questions_answers_to_json


def parse_args():
    parser = argparse.ArgumentParser(
        description='Download questions/answers from politicians from abgeordnetenwatch.de and export to csv or json.'
    )
    parser.add_argument('--id', '-i', type=int, help='Id of the politician to search for')
    parser.add_argument('--firstname', '-fn', type=str, help='Firstname of the politician to search for')
    parser.add_argument('--lastname', '-ln', type=str, help='Lastname of the politician to search for')
    # parser.add_argument('--party', '-p', type=str, help='Party of the politician to search for')

    parser.add_argument('--json', action='store_true', help='Output to json instead of csv')
    parser.add_argument('--outdir', '-o', type=str, default='data', help='The directory to save the file to')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show progress.')

    return parser, parser.parse_args()


def choose_from_list(politician_list) -> politicians.Politician:
    selected_politician = None
    print('found multiple politicians:')
    while selected_politician is None:
        for p in politician_list:
            print(f'  id={p.id}  \t{p.first_name}, {p.last_name}')
        politician_id = input('select one politician by id: ')
        try:
            politician_id = int(politician_id)
        except ValueError:
            print(f'\"{politician_id}\" is an invalid id! Try again.')
            continue
        result = [p for p in politician_list if p.id == politician_id]
        if len(result) != 1:
            print(f'No politician with id \"{politician_id}\" in the list.')
            continue
        selected_politician = result[0]
    return selected_politician


def main():
    parser, args = parse_args()

    filter_args = {}
    if args.firstname is not None:
        filter_args['first_name'] = args.firstname
    if args.lastname is not None:
        filter_args['last_name'] = args.lastname
    if args.id is not None:
        filter_args['id'] = args.id

    if not filter_args:
        parser.print_usage()
        print('Please provide at least --id --firstname or --lastname')
        sys.exit(1)

    politician_search_result = politicians.get_politicians(**filter_args)
    if len(politician_search_result) == 0:
        print('no politician found with the given arguments')
        sys.exit(1)
    elif len(politician_search_result) == 1:
        politician = politician_search_result[0]
    else:
        politician = choose_from_list(politician_search_result)

    if args.verbose:
        print(f'Downloading {politician}')

    questions_answers = politician.load_questions_answers(verbose=args.verbose)

    os.makedirs('data', exist_ok=True)
    ending = 'json' if args.json else 'csv'
    filename = f'data/{politician.id:0>6}_{politician.first_name}_{politician.last_name}.{ending}'
    if args.json:
        with open(filename, 'w') as f:
            data = questions_answers_to_json(questions_answers)
            json.dump(data, f, indent=2)
    else:
        questions_answers_to_csv(filename, questions_answers)

    if args.verbose:
        print('Saved result in', filename)


if __name__ == '__main__':
    main()

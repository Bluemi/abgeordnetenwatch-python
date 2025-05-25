import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import List

from abgeordnetenwatch_python.models import politicians
import questions_answers as qa


def parse_args():
    parser = argparse.ArgumentParser(
        description='Download questions/answers from politicians from abgeordnetenwatch.de and export to csv, txt or '
                    'json.'
    )
    parser.add_argument(
        '--url', type=str,
        help='Url of the politician to search for. '
             'For example https://www.abgeordnetenwatch.de/profile/firstname-lastname'
    )
    parser.add_argument('--id', '-i', type=int, help='Id of the politician to search for.')
    parser.add_argument('--firstname', '-fn', type=str, help='Firstname of the politician to search for.')
    parser.add_argument('--lastname', '-ln', type=str, help='Lastname of the politician to search for.')
    # parser.add_argument('--party', '-p', type=str, help='Party of the politician to search for')

    parser.add_argument(
        '--sort-by', type=str, default='question', choices=['answer', 'question'],
        help='Sort by date of question or answer. Can be one of the following: answer question. Defaults to answer.'
    )
    parser.add_argument('--threads', '-t', type=int, default=1, help='Number of threads to use for downloading.')

    parser.add_argument('--outdir', '-o', type=str, default='data', help='The directory to save the file to.')
    parser.add_argument('--quiet', '-q', action='store_true', help='Do not show progress.')

    return parser, parser.parse_args()


def choose_from_list(politician_list: List[politicians.Politician]) -> politicians.Politician:
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


async def async_main():
    parser, args = parse_args()

    politician = None

    url = args.url
    if url is not None:
        questions_answers = await qa.load_questions_answers(url, verbose=not args.quiet, threads=args.threads)
    else:
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

        if not args.quiet:
            print(f'Downloading {politician}')

        questions_answers = await politician.load_questions_answers(verbose=not args.quiet, threads=args.threads)

    # sort
    questions_answers = qa.sort_questions_answers(questions_answers, args.sort_by)

    os.makedirs('data', exist_ok=True)
    if politician is None:
        u = [u for u in url.split('/') if u][-1]
        filename = f'data/{u}.json'
    else:
        filename = f'data/{politician.id:0>6}_{politician.first_name}_{politician.last_name}.json'
    qa.save_answers_to_format(questions_answers, Path(filename), 'json')

    if not args.quiet:
        print('Saved result in', filename)


def main():
    asyncio.run(async_main())


if __name__ == '__main__':
    main()

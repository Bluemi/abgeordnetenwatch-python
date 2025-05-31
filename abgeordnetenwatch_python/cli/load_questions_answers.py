import argparse
import asyncio
import sys
from pathlib import Path
from typing import List

import aiohttp

from abgeordnetenwatch_python.models import politicians
from abgeordnetenwatch_python.models.politicians import get_default_filename
from abgeordnetenwatch_python.models.politician_dossier import load_politician_dossier_with_cache_file


def parse_args():
    parser = argparse.ArgumentParser(
        description='Download questions/answers from politicians from abgeordnetenwatch.de and export to csv, txt or '
                    'json.'
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
    parser.add_argument(
        '--cache-level', '-c', type=int, default=1,
        help='Cache level to use for requests.\n0: no cache.\n1: skip loaded questions, were the answer is cached.\n'
             '2: skip loaded questions.\n3: skip politicians that were loaded before.\nDefaults to 1.'
    )

    parser.add_argument(
        '--outdir', '-o', type=Path, default=Path('data') / 'json', help='The directory to save the file to.'
    )
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
    outdir: Path = args.outdir
    verbose = not args.quiet

    filter_args = {}
    if args.firstname is not None:
        filter_args['first_name'] = args.firstname
    if args.lastname is not None:
        filter_args['last_name'] = args.lastname
    if args.id is not None:
        filter_args['id'] = args.id

    if not filter_args:
        parser.print_usage()
        print('Please provide --id --firstname or --lastname')
        sys.exit(1)

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=args.threads)) as session:
        politician_search_result = await politicians.get_politicians(session=session, **filter_args)
        if len(politician_search_result) == 0:
            print('no politician found with the given arguments')
            return
        elif len(politician_search_result) == 1:
            politician = politician_search_result[0]
        else:
            politician = choose_from_list(politician_search_result)

        if verbose:
            print(f'Downloading {politician.first_name} {politician.last_name} {politician.id}')

        filename = get_default_filename(politician, outdir)
        await load_politician_dossier_with_cache_file(
            politician, filename, session=session, sort_by=args.sort_by, verbose=verbose, threads=args.threads
        )

    if verbose:
        print(f'Saved {str(politician)} to {filename}')


def main():
    asyncio.run(async_main())


if __name__ == '__main__':
    main()

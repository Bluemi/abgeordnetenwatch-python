import argparse
import json
from pathlib import Path

from parliament import get_parliament
from politicians import get_politician
from utils import sort_questions_answers, save_answers_to_format


def parse_args():
    parser = argparse.ArgumentParser(
        description='Download questions/answers from politicians from abgeordnetenwatch.de and export to csv, txt or '
                    'json.'
    )
    parser.add_argument(
        'parliament', type=str,
        help='Name of the parlament to download'
    )

    parser.add_argument(
        '--sort-by', type=str, default='question', choices=['answer', 'question'],
        help='Sort by date of question or answer. Can be one of the following: answer question. Defaults to answer.'
    )
    parser.add_argument('--n-threads', '-t', type=int, default=1, help='Number of threads to use for downloading.')

    parser.add_argument(
        '--format', type=str, default='csv', choices=['csv', 'json', 'txt'],
        help='Output format to use. One of the following: csv, json, txt. Defaults to csv.'
    )
    parser.add_argument('--outdir', '-o', type=Path, default=Path('data'), help='The directory to save the file to.')
    parser.add_argument('--quiet', '-q', action='store_true', help='Do not show progress.')

    return parser.parse_args()


def main():
    args = parse_args()

    verbose = not args.quiet

    outdir: Path = args.outdir / args.parliament.lower()
    outdir.mkdir(exist_ok=True, parents=True)
    meta_path = outdir / 'meta.json'

    if meta_path.is_file():
        with open(meta_path, 'r') as f:
            meta_data = json.load(f)
    else:
        print('loading politicians to scan:')
        parliament = get_parliament(label=args.parliament)
        politician_ids = parliament.get_politician_ids(verbose=verbose)
        print('found {} politicians'.format(len(politician_ids)))
        meta_data = [{'id': p, 'loaded': False} for p in politician_ids]
        with open(meta_path, 'w') as f:
            json.dump(meta_data, f)

    for index, pol_meta in enumerate(meta_data):
        politician_id, loaded = pol_meta['id'], pol_meta['loaded']
        if not loaded:
            try:
                politician = get_politician(id=politician_id)
                if verbose:
                    print('loading questions [{}/{}]: {}'.format(index + 1, len(meta_data), politician.get_full_name()))
                questions_answers = politician.load_questions_answers(verbose=not args.quiet, n_threads=args.n_threads)
                if len(questions_answers):
                    questions_answers = sort_questions_answers(questions_answers, args.sort_by)
                    ending = args.format
                    filename = outdir / f'{politician.id:0>6}_{politician.first_name}_{politician.last_name}.{ending}'

                    save_answers_to_format(questions_answers, filename, args.format)
                else:
                    if verbose:
                        print('Skipping {}. No questions found.'.format(politician.get_full_name()))
            except Exception as e:
                print('failed to load politician {}'.format(politician_id))
                print(e)

            meta_data[index]['loaded'] = True

            with open(meta_path, 'w') as f:
                json.dump(meta_data, f)


if __name__ == '__main__':
    main()

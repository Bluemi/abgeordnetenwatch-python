import argparse
import asyncio
from pathlib import Path

from abgeordnetenwatch_python.models.parliament import get_parliament
from abgeordnetenwatch_python.models.politicians import get_politician, get_default_filename
from abgeordnetenwatch_python.models.politician_dossier import load_politician_dossier_with_cache_file


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
    parser.add_argument('--threads', '-t', type=int, default=1, help='Number of threads to use for downloading.')

    parser.add_argument(
        '--outdir', '-o', type=Path, default=Path('data') / 'json', help='The directory to save the file to.'
    )
    parser.add_argument('--quiet', '-q', action='store_true', help='Do not show progress.')

    return parser.parse_args()


async def async_main():
    args = parse_args()

    verbose = not args.quiet

    outdir: Path = args.outdir / args.parliament.lower()
    outdir.mkdir(exist_ok=True, parents=True)

    print('loading politicians to scan:')
    parliament = get_parliament(label=args.parliament)
    politician_ids = parliament.get_politician_ids(verbose=verbose)
    print('found {} politicians'.format(len(politician_ids)))

    for index, politician_id in enumerate(politician_ids):
        try:
            politician = get_politician(id=politician_id)
            if verbose:
                print(f'loading questions [{index + 1}/{len(politician_ids)}]: {politician.get_full_name()}')

            filename = get_default_filename(politician, outdir)
            await load_politician_dossier_with_cache_file(
                politician, filename, threads=args.threads, verbose=verbose, sort_by=args.sort_by
            )
        except Exception as e:
            print('failed to load politician {}'.format(politician_id))
            print(e)


def main():
    asyncio.run(async_main())


if __name__ == '__main__':
    main()

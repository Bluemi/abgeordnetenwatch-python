import argparse

from parliament import get_parliaments


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
    parser.add_argument('--outdir', '-o', type=str, default='data', help='The directory to save the file to.')
    parser.add_argument('--quiet', '-q', action='store_true', help='Do not show progress.')

    return parser.parse_args()


def main():
    args = parse_args()

    parliaments = get_parliaments(label=args.parliament)
    print(parliaments)

    politicians = parliaments[0].get_politician_ids()
    print(politicians)


if __name__ == '__main__':
    main()

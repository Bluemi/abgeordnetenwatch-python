import argparse
from pathlib import Path
from typing import List
from tqdm import tqdm

from abgeordnetenwatch_python.questions_answers.load_qa import save_answers_to_format
from abgeordnetenwatch_python.models.politician_dossier import PoliticianDossier


def parse_args():
    parser = argparse.ArgumentParser(
        description='Convert questions/answers to csv, txt or json.'
    )
    parser.add_argument(
        'indir', type=Path, help='The directory to read files from.',
    )
    parser.add_argument(
        'outdir', type=Path, help='The directory to write converted files to.',
    )
    parser.add_argument(
        'format', type=str, choices=['csv', 'txt'],
        help='Output format to use. One of the following: csv, txt.'
    )
    parser.add_argument('--verbose', '-v', action='store_true', help='Show progress.')

    return parser.parse_args()


def list_files(indir: Path, file_format: str) -> List[Path]:
    return [p.relative_to(indir) for p in indir.rglob(f'*.{file_format}')]


def main():
    args = parse_args()
    indir = args.indir
    outdir = args.outdir
    out_format = args.format

    input_files = list_files(indir, 'json')

    outdir.mkdir(exist_ok=True, parents=True)

    if args.verbose:
        input_files = tqdm(input_files)

    for input_file in input_files:
        input_file = indir / input_file
        output_file = outdir / input_file.relative_to(indir).with_suffix('.' + out_format)

        output_file.parent.mkdir(exist_ok=True, parents=True)

        politician_dossier = PoliticianDossier.from_file(input_file)
        save_answers_to_format(politician_dossier.questions_answers, output_file, out_format)


if __name__ == '__main__':
    main()

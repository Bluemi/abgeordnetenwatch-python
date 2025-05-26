import argparse
from pathlib import Path
from typing import List
from tqdm import tqdm

from abgeordnetenwatch_python.questions_answers.load_qa import save_answers_to_format, parse_questions_answers


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
    format_choices = _get_format_choices()
    parser.add_argument(
        'format', type=str, choices=format_choices,
        help='Output format to use. One of the following: csv, json, txt. Defaults to csv.'
    )
    parser.add_argument('--verbose', '-v', action='store_true', help='Show progress.')

    return parser.parse_args()


def _get_format_choices():
    formats = ['csv', 'json', 'txt']
    choices = []
    for f1 in formats:
        for f2 in formats:
            if f1 != f2:
                choices.append(f'{f1}-{f2}')
    return choices


def list_files(indir: Path, file_format: str) -> List[Path]:
    return [p.relative_to(indir) for p in indir.rglob(f'*.{file_format}')]


def main():
    args = parse_args()
    indir = args.indir
    outdir = args.outdir
    in_format, out_format = args.format.split('-')

    input_files = list_files(indir, in_format)

    outdir.mkdir(exist_ok=True, parents=True)

    if args.verbose:
        input_files = tqdm(input_files)

    for input_file in input_files:
        input_file = indir / input_file
        output_file = outdir / input_file.relative_to(indir).with_suffix('.' + out_format)

        output_file.parent.mkdir(exist_ok=True, parents=True)

        questions_answers = parse_questions_answers(input_file, input_format=in_format)
        save_answers_to_format(questions_answers, output_file, out_format)


if __name__ == '__main__':
    main()

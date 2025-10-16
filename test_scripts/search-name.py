#!/usr/bin/env python3

import json
from pathlib import Path
from typing import Iterator, Tuple, List
from itertools import islice

from tqdm import tqdm

from abgeordnetenwatch_python.models.politician_dossier import PoliticianDossier
from abgeordnetenwatch_python.models.questions_answers import QuestionAnswerResult

DATA_DIR = Path("data/json/bundestag/")
NAME = "Max M."



def main():
    dossiers = LoadDossiers(DATA_DIR)
    lines = []
    for path, dossier in tqdm(dossiers):
        for qa in dossier.questions_answers.questions_answers:
            if str_in(qa.question, f"von {NAME}") or str_in(qa.question_addition, "von {NAME}"):
                add_question_to_lines(lines, qa)
    with open('karsten-fragen.txt', 'w') as f:
        f.writelines(lines)
    print('\n'.join(lines))


class LoadDossiers:
    def __init__(self, data_dir: Path, limit: int = -1):
        self.data_dir = data_dir
        json_files = data_dir.rglob("*.json")
        if limit > 0:
            json_files = islice(json_files, limit)
        self.json_files = sorted(list(json_files))

    def __iter__(self) -> Iterator[Tuple[Path, PoliticianDossier]]:
        for path in self.json_files:
            with open(path, 'r') as f:
                data = json.load(f)
                yield path, PoliticianDossier.model_validate(data)

    def __len__(self):
        return len(self.json_files)


def str_in(s, sub) -> bool:
    return s and sub in s


def add_question_to_lines(lines: List[str], qa: QuestionAnswerResult):
    question = qa.question or 'Frage konnte nicht geladen werden'
    lines.append('\n' + '-' * 50 + '\n')
    lines.append('Frage vom {}:\n'.format(qa.get_question_date()))
    lines.append(question)
    if qa.question_addition:
        lines.append('\nErläuterungen:')
        lines.append(qa.question_addition)
    if qa.answer:
        lines.append('\nAntwort vom {}:'.format(qa.get_answer_date()))
        lines.append(qa.answer)


if __name__ == '__main__':
    main()


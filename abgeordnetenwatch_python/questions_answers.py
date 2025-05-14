import csv
import datetime
import html.parser
import json
import asyncio
import re
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

import aiohttp
from bs4 import BeautifulSoup

import requests
from pydantic import BaseModel
from tqdm import tqdm


def normalize_base_url(base_url: str) -> str:
    profile_index = base_url.find('/profile/')
    base_url = base_url[profile_index:]

    base_url = '/'.join(base_url.split('/')[:3])

    if not base_url.endswith('/'):
        base_url += '/'
    return base_url + 'fragen-antworten/'


class QuestionsAnswersParser(html.parser.HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = normalize_base_url(base_url)
        self.hrefs = set()

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        if tag == 'a':
            attrs = dict(attrs)
            if 'href' in attrs:
                href = attrs['href']
                if href.startswith(self.base_url):
                    self.hrefs.add(href)

    def handle_endtag(self, tag: str):
        pass


def _date_to_str(date: Optional[datetime.date]) -> str:
    return date.strftime('%d.%m.%Y') if date is not None else 'XX.XX.XXXX'


class QuestionAnswerResult(BaseModel):
    url: Optional[str]
    question_date: Optional[datetime.date] = None
    question: Optional[str] = None
    question_addition: Optional[str] = None
    answer_date: Optional[datetime.date] = None
    answer: Optional[str] = None
    errors: List[str] = []

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'QuestionAnswerResult':
        new_data = data.copy()
        new_data['question_date'] = _str_to_date(data['question_date']) if data['question_date'] else None
        new_data['answer_date'] = _str_to_date(data['answer_date']) if data['answer_date'] else None
        return QuestionAnswerResult.model_validate(new_data)

    def get_question_date(self) -> str:
        return _date_to_str(self.question_date)

    def get_answer_date(self) -> str:
        return _date_to_str(self.answer_date)

    def __repr__(self) -> str:
        return ('QuestionAnswerResult(url={}, question_date={}, question={}, question_addition={}, '
                'answer_date={}, answer={})').format(
            self.url, self.get_question_date(), self.question, self.question_addition, self.get_answer_date(),
            self.answer
        )

    def __str__(self) -> str:
        return ('url={}\n  question_date={}\n  question={}\n  question_addition={}\n  answer_date={}\n  answer={}'
                .format(self.url, self.get_question_date(), self.question, self.question_addition,
                        self.get_answer_date(), self.answer)
                )


async def download_question_answer(url: str, session: aiohttp.ClientSession) -> QuestionAnswerResult:
    result = QuestionAnswerResult(url=url)
    async with session.get(url) as r:
        if r.ok:
            parse_question_answer(await r.text(), result)
        else:
            result.errors.append(f'Page download failed with code {r.status}')
    return result


def normalize_text(text: str) -> str:
    return ' '.join(filter(bool, text.strip().replace('\n', ' ').split(' ')))


def _parse_tag(tag):
    if tag:
        text = ' '.join(c.text for c in tag.children)
        return normalize_text(text)
    else:
        return None


def date_from_text(text: str) -> Optional[datetime.date]:
    try:
        return datetime.datetime.strptime(text[-10:], "%d.%m.%Y").date()
    except ValueError:
        return None


def parse_question_answer(content: str, qa_result: QuestionAnswerResult):
    soup = BeautifulSoup(content, 'html.parser')

    main_article = soup.find_all('article', {'itemtype': 'https://schema.org/Question'})[0]

    main_question_tag = main_article.find('h1', {'class': 'tile__question__teaser'})
    qa_result.question = _parse_tag(main_question_tag)

    addition_question_tag = main_article.find('div', {'class': 'tile__question-text'})
    qa_result.question_addition = _parse_tag(addition_question_tag)

    answer_tag = main_article.find('div', {'class': 'question-answer__text'})
    qa_result.answer = _parse_tag(answer_tag)

    # date infos
    question_date_tags = main_article.find_all('div', {'class': 'tile__politician__info'})
    if len(question_date_tags) >= 1:
        question_date_text = _parse_tag(question_date_tags[0])
        if question_date_text:
            qa_result.question_date = date_from_text(question_date_text)
    if len(question_date_tags) >= 2:
        answer_date_text = _parse_tag(question_date_tags[1])
        if answer_date_text is not None:
            qa_result.answer_date = date_from_text(answer_date_text)


def print_questions_answers(questions_answers: List[QuestionAnswerResult]):
    for qa_result in questions_answers:
        print('\n' + '-' * 50)
        print('\nurl:', qa_result.url)
        print(qa_result.get_question_date())
        print('FRAGE:')
        print(qa_result.question)
        if qa_result.question_addition is not None:
            print('ERLÄUTERUNG:')
            print(qa_result.question_addition)
        print('ANTWORT:')
        print(qa_result.get_answer_date())
        if qa_result.answer is not None:
            print(qa_result.answer)
        else:
            print('<keine Antwort>')


def questions_answers_to_json(filename: Path, questions_answers: List[QuestionAnswerResult]):
    def _default(obj):
        if isinstance(obj, datetime.date):
            return _date_to_str(obj)
        raise TypeError(f'Type {type(obj)} not serializable')
    data = [qa.model_dump() for qa in questions_answers]
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=_default)


def questions_answers_to_txt(filename: Path, questions_answers: List[QuestionAnswerResult]):
    with open(filename, 'w') as f:
        for qa in questions_answers:
            f.write('\n' + '-' * 50 + '\n\n')
            f.write('Frage vom {}:\n'.format(qa.get_question_date()))
            f.write(qa.question + '\n')
            if qa.question_addition:
                f.write('\nErläuterungen:\n')
                f.write(qa.question_addition + '\n')
            if qa.answer:
                f.write('\nAntwort vom {}:\n'.format(qa.get_answer_date()))
                f.write(qa.answer + '\n')


def questions_answers_to_csv(filename: Path, questions_answers: List[QuestionAnswerResult]):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['url', 'question_date', 'question', 'question_addition', 'answer_date', 'answer']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for qa in questions_answers:
            dump_data = qa.model_dump()
            dump_data = {key: dump_data[key] for key in fieldnames}
            writer.writerow(dump_data)


def save_answers_to_format(questions_answers: List[QuestionAnswerResult], filename: Path, fmt: str):
    if fmt == 'csv':
        questions_answers_to_csv(filename, questions_answers)
    elif fmt == 'json':
        questions_answers_to_json(filename, questions_answers)
    elif fmt == 'txt':
        questions_answers_to_txt(filename, questions_answers)


def parse_questions_answers(input_file: Path, input_format: Optional[str] = None) -> List[QuestionAnswerResult]:
    if input_format is None:
        input_format = input_file.suffix[1:]

    if input_format == 'txt':
        return parse_txt_file(input_file)
    elif input_format == 'json':
        with open(input_file, 'r') as f:
            data = json.load(f)
            return [QuestionAnswerResult.from_dict(d) for d in data]
    elif input_format == 'csv':
        results = []
        with open(input_file, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                results.append(QuestionAnswerResult.from_dict(row))
        return results
    else:
        raise ValueError('Unsupported file format: {}'.format(input_format))


def _str_to_date(date_text: str) -> datetime.date:
    return datetime.datetime.strptime(date_text, "%d.%m.%Y")


def parse_txt_file(input_file: Path) -> List[QuestionAnswerResult]:
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    entries = re.split(r'-{10,}', text.strip())
    result = []

    for entry in entries:
        if not entry.strip():
            continue

        question_date_match = re.search(r'Frage vom (\d{2}\.\d{2}\.\d{4}):', entry)
        question_match = re.search(r'Frage an .*', entry)
        addition_match = re.search(r'Erläuterungen:\s*(.*?)(Antwort vom|\Z)', entry, re.S)
        answer_date_match = re.search(r'Antwort vom (\d{2}\.\d{2}\.\d{4}):', entry)
        answer_match = re.search(r'Antwort vom \d{2}\.\d{2}\.\d{4}:\s*(.*)', entry, re.S)

        qa_result = QuestionAnswerResult.model_validate({
            "url": None,
            "question_date": _str_to_date(question_date_match.group(1)) if question_date_match else None,
            "question": question_match.group(0).strip() if question_match else None,
            "question_addition": addition_match.group(1).strip().replace('\n', ' ') if addition_match else None,
            "answer_date": _str_to_date(answer_date_match.group(1)) if answer_date_match else None,
            "answer": answer_match.group(1).strip().replace('\n', ' ') if answer_match else None,
            "errors": []
        })

        result.append(qa_result)

    return result


def sort_questions_answers(questions_answers: List[QuestionAnswerResult], sort_by: str):
    """
    Sort the given QuestionAnswerResults.

    :param questions_answers: The questions and answers to sort
    :param sort_by: The value to sort by. Either 'answer' or 'question'. Sorts by the date of the answer or the
                    question.
    :return: The same list, sorted by answer or question date.
    """
    if sort_by == 'answer':
        def _key_function(qa):
            if qa.answer_date:
                return qa.answer_date
            if qa.question_date:
                return qa.question_date
            return datetime.date.today()
    elif sort_by == 'question':
        def _key_function(qa):
            if qa.question_date:
                return qa.question_date
            return datetime.date.today()
    else:
        raise ValueError('Invalid sort option: {}'.format(sort_by))
    return list(sorted(questions_answers, key=_key_function))


def get_questions_answers_url(url: str, page: Optional[int] = None):
    if page is None:
        return '{}/{}'.format(url, 'fragen-antworten')
    else:
        return '{}/{}?page={}'.format(url, 'fragen-antworten', page)


def get_questions_answers_urls(url: str, verbose: bool = False) -> List[str]:
    """
    Load all question urls from a person.

    :param url: A base url like https://www.abgeordnetenwatch.de/profile/firstname-lastname/
    :param verbose: Whether to print verbose information
    :return: A list of urls, each pointing to a page with one question and optional answer
    """
    page = 0
    parser = QuestionsAnswersParser(url)
    while True:
        page_url = get_questions_answers_url(url, page)
        page += 1
        r = requests.get(page_url)
        if r.ok:
            old_count = len(parser.hrefs)
            parser.feed(r.text)
            if old_count == len(parser.hrefs):
                break
        else:
            break

    if verbose:
        print('{} questions answers found'.format(len(parser.hrefs)))

    return ['https://www.abgeordnetenwatch.de' + href for href in parser.hrefs]


async def async_get_questions_answers_urls(
        url: str, session: aiohttp.ClientSession, verbose: bool = False, threads: int = 5,
) -> List[str]:
    parser = QuestionsAnswersParser(url)
    sem = asyncio.Semaphore(threads)

    async def fetch_page(page: int):
        page_url = get_questions_answers_url(url, page)
        async with sem, session.get(page_url) as resp:
            if resp.status != 200:
                return None
            return await resp.text()

    pages = 0
    pbar = None
    if verbose:
        pbar = tqdm(desc="collecting questions")
    while True:
        tasks = [asyncio.create_task(fetch_page(p)) for p in range(pages, pages + threads)]
        old_count = len(parser.hrefs)
        for coro in asyncio.as_completed(tasks):
            text = await coro
            if pbar is not None:
                pbar.update(1)
            if text:
                parser.feed(text)
        if len(parser.hrefs) == old_count:
            break
        pages += threads

    if pbar is not None:
        pbar.close()

    if verbose:
        print(f"{len(parser.hrefs)} questions answers found")

    return [str('https://www.abgeordnetenwatch.de' + href) for href in parser.hrefs]


async def load_questions_answers(
        politician_url: str, verbose: bool = False, threads: int = 1
) -> List[QuestionAnswerResult]:
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=threads)) as session:
        urls = await async_get_questions_answers_urls(politician_url, session, verbose=verbose, threads=threads)

        tasks = [download_question_answer(url, session) for url in urls]
        results = []
        for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc='loading questions'):
            results.append(await coro)

    return results

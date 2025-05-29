import csv
import datetime
import html.parser
import json
import asyncio
import re
from pathlib import Path
from typing import List, Optional, Tuple, Iterable

import aiohttp
from bs4 import BeautifulSoup

import requests
from tqdm import tqdm

from models.questions_answers import QuestionAnswerResult, str_to_date, \
    QuestionsAnswers
from abgeordnetenwatch_python.cache import (CacheSettings, load_questions_answers_cache, QuestionsAnswerCache,
                                            dump_questions_answers_cache)


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


async def download_question_answer(
        url: str, session: aiohttp.ClientSession, cache_settings: CacheSettings, cache: QuestionsAnswerCache
) -> QuestionAnswerResult:
    if cache:
        cached_result = cache.get_by_url(url)
        if cache_settings.cache_url(cached_result):
            return cached_result
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


def print_questions_answers(questions_answers: QuestionsAnswers):
    for qa_result in questions_answers.questions_answers:
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


def questions_answers_to_json(filename: Path, questions_answers: QuestionsAnswers):
    data = questions_answers.model_dump(mode='json')
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


def questions_answers_to_txt(filename: Path, questions_answers: QuestionsAnswers):
    with open(filename, 'w') as f:
        for qa in questions_answers.questions_answers:
            f.write('\n' + '-' * 50 + '\n\n')
            f.write('Frage vom {}:\n'.format(qa.get_question_date()))
            f.write(qa.question + '\n')
            if qa.question_addition:
                f.write('\nErläuterungen:\n')
                f.write(qa.question_addition + '\n')
            if qa.answer:
                f.write('\nAntwort vom {}:\n'.format(qa.get_answer_date()))
                f.write(qa.answer + '\n')


def questions_answers_to_csv(filename: Path, questions_answers: QuestionsAnswers):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['url', 'question_date', 'question', 'question_addition', 'answer_date', 'answer']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for qa in questions_answers.questions_answers:
            dump_data = qa.model_dump(mode='json')
            dump_data = {key: dump_data[key] for key in fieldnames}
            writer.writerow(dump_data)


def save_answers_to_format(questions_answers: QuestionsAnswers, filename: Path, fmt: str):
    if fmt == 'csv':
        questions_answers_to_csv(filename, questions_answers)
    elif fmt == 'json':
        questions_answers_to_json(filename, questions_answers)
    elif fmt == 'txt':
        questions_answers_to_txt(filename, questions_answers)


def parse_questions_answers(input_file: Path, input_format: Optional[str] = None) -> QuestionsAnswers:
    if input_format is None:
        input_format = input_file.suffix[1:]

    if input_format == 'txt':
        return parse_txt_file(input_file)
    elif input_format == 'json':
        with open(input_file, 'r') as f:
            data = json.load(f)
            return QuestionsAnswers.model_validate(data)
    elif input_format == 'csv':
        results = []
        with open(input_file, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                results.append(QuestionAnswerResult.model_validate(row))
        return QuestionsAnswers(questions_answers=results)
    else:
        raise ValueError('Unsupported file format: {}'.format(input_format))


def parse_txt_file(input_file: Path) -> QuestionsAnswers:
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    entries = re.split(r'-{10,}', text.strip())
    questions_answers = []

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
            "question_date": str_to_date(question_date_match.group(1)) if question_date_match else None,
            "question": question_match.group(0).strip() if question_match else None,
            "question_addition": addition_match.group(1).strip().replace('\n', ' ') if addition_match else None,
            "answer_date": str_to_date(answer_date_match.group(1)) if answer_date_match else None,
            "answer": answer_match.group(1).strip().replace('\n', ' ') if answer_match else None,
            "errors": []
        })

        questions_answers.append(qa_result)

    return QuestionsAnswers(questions_answers=questions_answers)


def sort_questions_answers(questions_answers: QuestionsAnswers, sort_by: str):
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
    questions_answers = list(sorted(questions_answers.questions_answers, key=_key_function))
    return QuestionsAnswers(questions_answers=questions_answers)


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

    async def fetch_page(page_index: int):
        page_url = get_questions_answers_url(url, page_index)
        async with sem, session.get(page_url) as resp:
            if resp.status != 200:
                return None
            return await resp.text()

    pages = 0
    pbar = None
    if verbose:
        pbar = tqdm(desc="collecting questions")
    running = True
    while running:
        tasks = [asyncio.create_task(fetch_page(p)) for p in range(pages, pages + threads)]
        for page_text in await asyncio.gather(*tasks):
            if pbar is not None:
                pbar.update(1)
            old_count = len(parser.hrefs)
            if page_text:
                parser.feed(page_text)

            # if no new urls here, stop searching for more
            running = len(parser.hrefs) != old_count
        pages += threads

    if pbar is not None:
        pbar.close()

    if verbose:
        print(f"{len(parser.hrefs)} questions answers found")

    return [str('https://www.abgeordnetenwatch.de' + href) for href in parser.hrefs]


def get_batches(frames: List, batch_size: int) -> Iterable[List]:
    """
    Cuts the given list in chunks and yields them one by one.

    :param frames: The list to cut
    :param batch_size: The size of each batch
    """
    index = 0
    while True:
        chunk = frames[index:index+batch_size]
        yield chunk
        index += batch_size
        if index >= len(frames):
            break


async def load_questions_answers(
        politician_url: str, verbose: bool = False, threads: int = 1, cache_settings: Optional[CacheSettings] = None,
) -> QuestionsAnswers:
    cache = load_questions_answers_cache(cache_settings, politician_url)

    # if cache level == 3: cache everything, if the file exists
    if cache and cache_settings.cache_urls():
        return QuestionsAnswers(questions_answers=cache.questions_answers)

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=threads)) as session:
        urls = await async_get_questions_answers_urls(
            politician_url, session, verbose=verbose, threads=threads
        )

        progress = None
        if verbose:
            progress = tqdm(total=len(urls), desc="loading questions")
        results: List[QuestionAnswerResult] = []
        for url_batch in get_batches(urls, threads):
            tasks = [download_question_answer(url, session, cache_settings, cache) for url in url_batch]
            for coro in asyncio.as_completed(tasks):
                results.append(await coro)
                if progress is not None:
                    progress.update(1)

    dump_questions_answers_cache(cache_settings, politician_url, QuestionsAnswerCache.new(results))

    return QuestionsAnswers(questions_answers=results)

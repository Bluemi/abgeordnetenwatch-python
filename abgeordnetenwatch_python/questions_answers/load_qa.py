import csv
import datetime
import functools
import html.parser
import json
import asyncio
import re
import warnings
from pathlib import Path
from typing import List, Optional, Tuple, Iterable, Set

import aiohttp
from bs4 import BeautifulSoup

from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio

from abgeordnetenwatch_python.models.questions_answers import QuestionAnswerResult, str_to_date, QuestionsAnswers, \
    TqdmArgs, normalize_tqdm_args
from abgeordnetenwatch_python.cache import CacheInfo


def normalize_base_url(base_url: str) -> str:
    profile_index = base_url.find('/profile/')
    base_url = base_url[profile_index:]

    base_url = '/'.join(base_url.split('/')[:3])

    if not base_url.endswith('/'):
        base_url += '/'
    return base_url + 'fragen-antworten/'


class QuestionsAnswersParser(html.parser.HTMLParser):
    def __init__(self, base_url: str, hrefs: Optional[Set[str]] = None):
        super().__init__()
        self.base_url = normalize_base_url(base_url)
        self.hrefs = hrefs if hrefs is not None else set()

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
        url: str, session: aiohttp.ClientSession, cache_info: Optional[CacheInfo]
) -> QuestionAnswerResult:
    cached_result = None
    if cache_info:
        cached_result = cache_info.get_by_url(url)
        if cache_info.should_cache(cached_result):
            return cached_result
    result = QuestionAnswerResult(url=url)
    async with session.get(url) as r:
        if r.ok:
            parse_question_answer(await r.text(), result)
            if cached_result is not None and cached_result.answer is None and result.answer is not None:
                if cache_info.num_answers_missing == 0:
                    warnings.warn(f'Found answer, but did not expect to find one more.')
                cache_info.num_answers_missing -= 1
        else:
            result.errors.append(f'Page download for "{url}" failed with code {r.status}')
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
            question = qa.question or 'Frage konnte nicht runtergeladen werden'
            f.write('\n' + '-' * 50 + '\n\n')
            f.write('Frage vom {}:\n'.format(qa.get_question_date()))
            f.write(question + '\n')
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


async def async_get_questions_answers_urls(
        url: str, session: aiohttp.ClientSession, cache_info: Optional[CacheInfo] = None, verbose: bool = False,
        threads: int = 5, tqdm_args: Optional[TqdmArgs] = None,
        politician_name: Optional[str] = None,
) -> List[str]:
    sem = asyncio.Semaphore(threads)
    base_url = 'https://www.abgeordnetenwatch.de'

    async def fetch_page(page_index: int):
        page_url = get_questions_answers_url(url, page_index)
        async with sem, session.get(page_url) as resp:
            if resp.status != 200:
                return None
            return await resp.text()

    total = None
    all_urls = set()
    # if we know how many questions are missing ...
    if cache_info is not None and cache_info.num_questions_missing != -1:
        # ... then, we know the number of questions missing + the cached questions = all questions
        total = len(cache_info.questions_answers) + cache_info.num_questions_missing
        all_urls = set([qa.url.removeprefix(base_url) for qa in cache_info.questions_answers.questions_answers])

    parser = QuestionsAnswersParser(url, all_urls)
    pages = 0
    pbar = None
    if verbose:
        tqdm_args = normalize_tqdm_args(tqdm_args, f'collecting {politician_name or 'questions'}')
        pbar = tqdm(total=total, **tqdm_args)
        pbar.update(len(all_urls))
    running = True
    while running:
        # if we found all urls, stop searching for more
        if total is not None and len(all_urls) >= total:
            if len(all_urls) > total:
                warnings.warn(f'Found more questions than expected. Expected {total}, found {len(all_urls)}')
            break

        tasks = [asyncio.create_task(fetch_page(p)) for p in range(pages, pages + threads)]
        for page_text in await asyncio.gather(*tasks):
            old_count = len(all_urls)
            if page_text:
                parser.feed(page_text)

            # if no new urls here, stop searching for more
            running = len(all_urls) != old_count
            if pbar is not None:
                pbar.update(len(all_urls) - old_count)
            if cache_info is not None and not cache_info.is_question_missing():
                running = False
        pages += threads

    if total is not None:
        if total != len(all_urls):
            warnings.warn(f'Expected {total} questions, but found {len(all_urls)}')

    if pbar is not None:
        pbar.close()

    return [str(base_url + href) for href in all_urls]


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
        politician_url: str, session: aiohttp.ClientSession, verbose: bool = False, threads: int = 1,
        url_threads: int = -1, cache_info: Optional[CacheInfo] = None, tqdm_args: TqdmArgs = None,
        politician_name: Optional[str] = None,
) -> QuestionsAnswers:
    if url_threads == -1:
        url_threads = threads

    urls = await async_get_questions_answers_urls(
        politician_url, session, cache_info=cache_info, verbose=verbose, threads=url_threads, tqdm_args=tqdm_args,
        politician_name=politician_name
    )

    gather_func = asyncio.gather
    if verbose:
        tqdm_args = normalize_tqdm_args(tqdm_args, f"loading {politician_name or 'questions'}")
        gather_func = functools.partial(tqdm_asyncio.gather, total=len(urls), **tqdm_args)
    tasks = [download_question_answer(url, session, cache_info) for url in urls]
    results: List[QuestionAnswerResult] = await gather_func(*tasks)

    return QuestionsAnswers(questions_answers=results)

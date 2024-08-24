import concurrent.futures
import csv
import datetime
import html.parser
from typing import List, Optional

from bs4 import BeautifulSoup

import requests
import tqdm


def normalize_base_url(base_url):
    profile_index = base_url.find('/profile/')
    base_url = base_url[profile_index:]

    base_url = '/'.join(base_url.split('/')[:3])

    if not base_url.endswith('/'):
        base_url += '/'
    return base_url + 'fragen-antworten/'


class QuestionsAnswersParser(html.parser.HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.base_url = normalize_base_url(base_url)
        self.hrefs = set()

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attrs = dict(attrs)
            if 'href' in attrs:
                href = attrs['href']
                if href.startswith(self.base_url):
                    self.hrefs.add(href)

    def handle_endtag(self, tag):
        pass


class QuestionAnswerResult:
    def __init__(self, url: str):
        self.url = url
        self.question_date = None
        self.question = None
        self.question_addition = None
        self.answer_date = None
        self.answer = None
        self.errors = []

    def to_json(self):
        return dict(
            url=self.url,
            question=self.question,
            question_addition=self.question_addition,
            answer=self.answer,
            question_date=self.get_question_date(),
            answer_date=self.get_answer_date(),
        )

    def get_question_date(self) -> str:
        return self.question_date.strftime('%d.%m.%Y') if self.question_date is not None else 'XX.XX.XXXX'

    def get_answer_date(self) -> str:
        return self.answer_date.strftime('%d.%m.%Y') if self.answer_date is not None else 'XX.XX.XXXX'

    def __repr__(self):
        return ('QuestionAnswerResult(url={}, question_date={}, question={}, question_addition={}, '
                'answer_date={}, answer={})').format(
            self.url, self.get_question_date(), self.question, self.question_addition, self.get_answer_date(),
            self.answer
        )

    def __str__(self):
        return ('url={}\n  question_date={}\n  question={}\n  question_addition={}\n  answer_date={}\n  answer={}'
                .format(self.url, self.get_question_date(), self.question, self.question_addition,
                        self.get_answer_date(), self.answer)
                )


def download_question_answer(url) -> QuestionAnswerResult:
    result = QuestionAnswerResult(url)
    r = requests.get(url)
    if r.ok:
        parse_question_answer(r.text, result)
    else:
        result.errors.append(f'Page download failed with code {r.status_code}')
    return result


def normalize_text(text):
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


def parse_question_answer(content, qa_result: QuestionAnswerResult):
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


def questions_answers_to_json(questions_answers: List[QuestionAnswerResult]):
    return [qa.to_json() for qa in questions_answers]


def questions_answers_to_txt(filename, questions_answers: List[QuestionAnswerResult]):
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


def questions_answers_to_csv(filename, questions_answers: List[QuestionAnswerResult]):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['url', 'question_date', 'question', 'question_addition', 'answer_date', 'answer']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for qa in questions_answers:
            writer.writerow(qa.to_json())


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


def get_questions_answers_url(url, page=None):
    if page is None:
        return '{}/{}'.format(url, 'fragen-antworten')
    else:
        return '{}/{}?page={}'.format(url, 'fragen-antworten', page)


def get_questions_answers_urls(url, verbose=False):
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


def load_questions_answers(politician_url, verbose=False, n_threads=1) -> List[QuestionAnswerResult]:
    urls = get_questions_answers_urls(politician_url, verbose=verbose)
    if n_threads == 1:
        if verbose:
            urls = tqdm.tqdm(urls, desc='Loading questions answers', ascii=True)
        return [download_question_answer(url) for url in urls]
    elif n_threads > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [executor.submit(download_question_answer, url=url) for url in urls]
            if verbose:
                futures = tqdm.tqdm(futures, desc='Loading questions answers', ascii=True)
            return [f.result() for f in futures]
    else:
        raise ValueError('n_threads must be 1 or greater, got {}'.format(n_threads))


def save_page(politician):
    url = politician.get_url()
    url = get_questions_answers_url(url, 0)

    r = requests.get(url)
    print(r.status_code)
    name = '{}_{}'.format(politician.first_name, politician.last_name)
    with open(f'pages/{name}.html', 'w') as f:
        f.write(r.text)

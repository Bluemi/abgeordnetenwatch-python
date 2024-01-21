import csv
import datetime
import html.parser
from typing import List, Optional

from bs4 import BeautifulSoup

import requests


def get_from_key_list(key_list, key, default=None):
    for k, value in key_list:
        if k == key:
            return value
    return default


class QuestionsAnswersParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_div = False
        self.hrefs = set()

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            if 'tile__question__teaser' in get_from_key_list(attrs, 'class', ''):
                self.in_div = True
        elif tag == 'a':
            if self.in_div:
                href = get_from_key_list(attrs, 'href', None)
                if href:
                    if not href.split('/')[-1].isnumeric():
                        self.hrefs.add(href)

    def handle_endtag(self, tag):
        if tag == 'div':
            self.in_div = False


class QuestionAnswerParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = None

        self.in_question = False
        self.question = None

    def handle_starttag(self, tag, attrs):
        if tag == 'h1' and get_from_key_list(attrs, 'class', '') == 'tile__question__teaser':
            self.in_title = True
        elif tag == 'div' and get_from_key_list(attrs, 'class', '') == 'field field--text_long field--text':
            self.in_question = True

    def handle_endtag(self, tag):
        if tag == 'h1':
            self.in_title = False
        if tag == 'div':
            self.in_question = False

    def handle_data(self, data):
        if self.in_title:
            self.title = ' '.join(t for t in data.strip().replace('\n', ' ').split(' ') if t)
        if self.in_question:
            if self.question is None:
                self.question = ' '.join(t for t in data.strip().replace('\n', ' ').split(' ') if t)


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


def questions_answers_to_csv(filename, questions_answers: List[QuestionAnswerResult]):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['url', 'question_date', 'question', 'question_addition', 'answer_date', 'answer']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for qa in questions_answers:
            writer.writerow(qa.to_json())

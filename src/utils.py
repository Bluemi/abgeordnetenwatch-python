import html.parser
from typing import Optional, Tuple

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


def download_question_answers(url) -> Tuple[Optional[str], Optional[str]]:
    r = requests.get(url)
    if r.ok:
        return parse_question_answer(r.text)


def parse_question_answer(content) -> Tuple[Optional[str], Optional[str]]:
    soup = BeautifulSoup(content, 'html.parser')
    question_tag = soup.find('div', {'class': 'tile__question-text'})
    question = None
    if question_tag:
        question = ' '.join(filter(bool, question_tag.div.p.string.strip().split(' ')))

    answer_tag = soup.find('div', {'class': 'question-answer__text'})
    answer = None
    if answer_tag:
        answer = ' '.join(filter(bool, answer_tag.div.text.strip().split(' ')))

    return question, answer

import enum
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


class DownloadResult:
    class ErrorCode(enum.Enum):
        OK = 0
        UNINITIALIZED = 1
        PAGE_DOWNLOAD_FAILED = 2
        QUESTION_PARSING_FAILED = 3
        ANSWER_PARSING_FAILED = 4
        ANSWER_TAG_NOT_FOUND = 5
        QUESTION_TAG_NOT_FOUND = 6

    def __init__(self, content: str = None, url: str = None, error_code: int = ErrorCode.UNINITIALIZED, error_text: str = None):
        self.content = content
        self.url = url
        self.error_code = error_code
        self.error_text = error_text

    def ok(self):
        return self.error_code == DownloadResult.ErrorCode.OK

    def set_content(self, content: str = None):
        self.content = content
        self.error_code = DownloadResult.ErrorCode.OK

    def failed(self, error_code: ErrorCode, error_text: str):
        self.error_code = error_code
        self.error_text = error_text


def download_question_answer(url) -> Tuple[DownloadResult, DownloadResult]:
    question_download_result = DownloadResult(url=url)
    answer_download_result = DownloadResult(url=url)
    r = requests.get(url)
    if r.ok:
        parse_question_answer(r.text, question_download_result, answer_download_result)
    else:
        question_download_result.failed(
            DownloadResult.ErrorCode.PAGE_DOWNLOAD_FAILED, f'Page download failed with code {r.status_code}'
        )
        answer_download_result.failed(
            DownloadResult.ErrorCode.PAGE_DOWNLOAD_FAILED, f'Page download failed with code {r.status_code}'
        )
    return question_download_result, answer_download_result


def parse_question_answer(content, question_result, answer_result):
    soup = BeautifulSoup(content, 'html.parser')
    question_tag = soup.find('div', {'class': 'tile__question-text'})
    if question_tag:
        try:
            question = ' '.join(filter(bool, question_tag.div.p.string.strip().split(' ')))
            question_result.set_content(question)
        except AttributeError as e:
            question_result.failed(DownloadResult.ErrorCode.QUESTION_PARSING_FAILED, repr(e))
    else:
        question_result.failed(DownloadResult.ErrorCode.ANSWER_TAG_NOT_FOUND)

    answer_tag = soup.find('div', {'class': 'question-answer__text'})
    if answer_tag:
        try:
            answer = ' '.join(filter(bool, answer_tag.div.text.strip().split(' ')))
            answer_result.set_content(answer)
        except AttributeError as e:
            answer_result.failed(DownloadResult.ErrorCode.ANSWER_PARSING_FAILED, repr(e))
    else:
        answer_result.failed(DownloadResult.ErrorCode.ANSWER_TAG_NOT_FOUND)


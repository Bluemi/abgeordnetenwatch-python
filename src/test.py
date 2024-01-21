import requests
from bs4 import BeautifulSoup

import politicans
from utils import parse_question_answer, DownloadResult, print_questions_answers


def main():
    with open('data/question-answer-page.html', 'r') as f:
        data = f.read()
    soup = BeautifulSoup(data, 'html.parser')
    question_tag = soup.find('div', {'class': 'tile__question-text'})
    if question_tag:
        question = question_tag.div.p.string

    answer_tag = soup.find('div', {'class': 'question-answer__text'})
    if answer_tag:
        answer = ' '.join(filter(bool, answer_tag.div.text.strip().split(' ')))


def main2():
    example_politician = politicans.get_politicians(first_name='')[0]
    # print(example_politician)
    questions_answers = example_politician.load_questions_answers()

    print_questions_answers(questions_answers)


def download_page():
    r = requests.get('https://www.abgeordnetenwatch.de')
    with open('pages/test3.html', 'w') as f:
        f.write(r.text)


def test_page_parsing(text):
    question_download_result = DownloadResult()
    answer_download_result = DownloadResult()
    info_download_result = DownloadResult()

    parse_question_answer(text, question_download_result, answer_download_result, info_download_result)

    print(question_download_result.content)
    # print('#' * 20)
    # print(answer_download_result.content)


def main3():
    for page in ['pages/test1.html', 'pages/test2.html']:
        with open(page, 'r') as f:
            text = f.read()
        print('page:', page)
        test_page_parsing(text)


if __name__ == '__main__':
    main2()

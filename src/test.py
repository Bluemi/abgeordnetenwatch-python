import requests
from bs4 import BeautifulSoup

import politicans
import utils
from utils import print_questions_answers


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
    example_politician = politicans.get_politicians(first_name='', last_name='')[0]
    # print(example_politician)
    questions_answers = example_politician.load_questions_answers(verbose=True)

    print_questions_answers(questions_answers)

    utils.questions_answers_to_csv('data/amira_mohamed_ali.csv', questions_answers)


def main4():
    result = utils.download_question_answer('https://www.abgeordnetenwatch.de/profile/joana-cotar/fragen-antworten/hallo-frau-cotar-kaeme-fuer-sie-aufgrund-der-aktuellen-ereignisse-eine-mitgliedschaft-im-bsw-in-frage')
    print(str(result))

    print('-' * 50)

    result = utils.download_question_answer('https://www.abgeordnetenwatch.de/profile/astrid-wallmann/fragen-antworten/wie-kann-die-finanzielle-ungerechtigkeit-der-krankenversicherungen-fuer-gesunde-bzw-schwerbehinderte-geloest')
    print(str(result))

    print('-' * 50)

    result = utils.download_question_answer('https://www.abgeordnetenwatch.de/profile/markus-ferber/fragen-antworten/welche-massnahmen-gegen-geldwaesche-waeren-ihrer-meinung-nach-zielfuehrender-als-die-limitierung-der-hoehe-von')
    print(str(result))


def download_page():
    r = requests.get('https://www.abgeordnetenwatch.de')
    with open('pages/test3.html', 'w') as f:
        f.write(r.text)


def main3():
    for page in ['pages/test1.html', 'pages/test2.html']:
        with open(page, 'r') as f:
            text = f.read()
        print('page:', page)


if __name__ == '__main__':
    main2()

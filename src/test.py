from bs4 import BeautifulSoup


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


if __name__ == '__main__':
    main()

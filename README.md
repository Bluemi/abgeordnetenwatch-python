# abgeordnetenwatch-python

Siehe [hier](README_de.md) für die deutsche Anleitung.

Small utility programs to use the [abgeordnetenwatch-api](https://www.abgeordnetenwatch.de/) in python.

## Installation

To use this script install [python3](https://www.python.org/) and [pip](https://packaging.python.org/en/latest/tutorials/installing-packages/).

Install requirements with
```sh
pip install -r requirements.txt
```

## Usage

You can download all questions and answers from a politician with the following script:

```sh
# -v for verbose output
python3 src/load_questions_answers.py --firstname "Angela" --lastname "Merkel"

# for more options
python3 src/load_questions_answers.py --help
```

This will create a file `data/079137_Angela_Merkel.csv` with all questions and answers of the specified person.

### Load Parliament
To fetch all questions and answers from all politicians from a parliament you can do the following:
```sh
# load "bundestag" using 16 requests simulaneously
python3 src/load_parliament_qa.py bundestag -t 16

# for more options
python3 src/load_parliament_qa.py --help
```

# abgeordnetenwatch-python

Siehe [hier](README_de.md) für die deutsche Anleitung.

Small utility programs to use the [abgeordnetenwatch-api](https://www.abgeordnetenwatch.de/) in python.

## Installation

To use this script install [python3](../blob/master/LICENSE) and [pip](https://packaging.python.org/en/latest/tutorials/installing-packages/).

Install requirements with
```sh
pip install -r requirements.txt
```

## Usage

You can download all questions and answers from a politician with the following script:

```sh
# -v for verbose output
python3 src/load_questions_answers.py -v --firstname "Angela" --lastname "Merkel"

# try this for more options
python3 src/load_questions_answers.py --help
```

This will create a file `data/079137_Angela_Merkel.csv.csv` with all questions and answers of the specified person.

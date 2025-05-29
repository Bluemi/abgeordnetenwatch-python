# abgeordnetenwatch-python

Siehe [hier](README_de.md) für die deutsche Anleitung.

Small utility programs to use the [abgeordnetenwatch-api](https://www.abgeordnetenwatch.de/) in python.

## Installation

To use this script, install [python3](https://www.python.org/) and [pip](https://packaging.python.org/en/latest/tutorials/installing-packages/).

Install requirements with
```sh
pip install .
```

## Usage

You can download all questions and answers from a politician with the following script:

```sh
# -v for verbose output
load_questions_answers --firstname "Angela" --lastname "Merkel"

# for more options
load_questions_answers --help
```

This will create a file `data/json/079137_Angela_Merkel.json` with all questions and answers of the specified person.

### Converting to txt files
To convert json files to txt, do the following:

```sh
convert_qa data/json data/txt txt

# convert to csv
convert_qa data/json data/csv csv
```

This will create a file `data/txt/079137_Angela_Merkel.txt` (for all files in `data/json`).

### Load Parliament
To fetch all questions and answers from all politicians from a parliament, you can do the following:
```sh
# load "bundestag" using 16 requests simulaneously
load_parliament_qa bundestag -t 16

# for more options
load_parliament_qa --help
```

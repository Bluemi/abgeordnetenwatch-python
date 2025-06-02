# abgeordnetenwatch-python

Kleine Programme zur Nutzung der [abgeordnetenwatch-api](https://www.abgeordnetenwatch.de/) in Python.

## Installation

Vorher [python3](https://www.python.org/) und [pip](https://packaging.python.org/en/latest/tutorials/installing-packages/) installieren.

```sh
pip install abgeordnetenwatch-python
```

## Verwendung

Alle Fragen und Antworten eines Politikers mit dem folgenden Skript herunterladen:

```sh
# -v für ausführliche Ausgabe
load_questions_answers --firstname angela --lastname merkel

# für weitere Optionen
load_questions_answers --help
```

Dies erzeugt eine Datei `data/json/079137_Angela_Merkel.json` mit allen Fragen und Antworten der angegebenen Person.

### Konvertierung in txt-Dateien

```sh
convert_qa data/json data/txt txt

# Konvertieren nach csv
convert_qa data/json data/csv csv
```

Dies erstellt eine Datei `data/txt/079137_Angela_Merkel.txt` (für alle Dateien in `data/json`).

### Parlament laden
Alle Fragen und Antworten von allen Politikern aus einem Parlament herunterladen:
```sh
# lade „bundestag“ mit 16 gleichzeitigen Anfragen
load_parliament_qa bundestag -t 16

# für weitere Optionen
load_parliament_qa --help
```


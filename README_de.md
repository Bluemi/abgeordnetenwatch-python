# abgeordnetenwatch-python

Kleine Programme zur Nutzung der [abgeordnetenwatch-api](https://www.abgeordnetenwatch.de/) in Python.

## Installation

Um dieses Skript zu verwenden, installieren Sie [python3](https://www.python.org/) und [pip](https://packaging.python.org/en/latest/tutorials/installing-packages/).

Installieren Sie die Anforderungen mit
```sh
pip install .
```

## Verwendung

Sie können alle Fragen und Antworten eines Politikers mit dem folgenden Skript herunterladen:

```sh
# -v für ausführliche Ausgabe
load_questions_answers --firstname angela --lastname merkel

# für weitere Optionen
load_questions_answers --help
```

Dies wird eine Datei `data/json/079137_Angela_Merkel.json` mit allen Fragen und Antworten der angegebenen Person erstellen.

### Konvertierung in txt-Dateien
Um json-Dateien in txt-Dateien zu konvertieren, gehen Sie wie folgt vor:

```sh
convert_qa data/json data/txt txt

# Konvertieren nach csv
convert_qa data/json data/csv csv
```

Dies wird eine Datei `data/txt/079137_Angela_Merkel.txt` erstellen (für alle Dateien in `data/json`).

### Parlament laden
Um alle Fragen und Antworten von allen Politikern aus einem Parlament zu holen, können Sie folgendes tun:
```sh
# lade „bundestag“ mit 16 gleichzeitigen Anfragen
load_parliament_qa bundestag -t 16

# für weitere Optionen
load_parliament_qa --help
```


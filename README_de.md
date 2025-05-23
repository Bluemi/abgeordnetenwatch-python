# AbgeordnetenWatch-Python

Einige hilfreiche Skripte, um auf die [Abgeordnetenwatch-API](https://www.abgeordnetenwatch.de/) in python zugreifen zu können.

## Installation

Um dieses Skript verwenden zu können, müssen Sie [python3](https://www.python.org/) und [pip](https://packaging.python.org/en/latest/tutorials/installing-packages/) installiert haben.

Danach Abhängigkeiten mit folgendem Befehl installieren
```sh
pip install -r requirements.txt
```

## Nutzung

Sie können alle [Fragen und Antworten](https://www.abgeordnetenwatch.de/) eines Politikers mit dem folgenden Skript herunterladen:

```sh
# -v um mehr informationen während des Downloads anzuzeigen
python3 abgeordnetenwatch-python/load_questions_answers.py --firstname "Angela" --lastname "Merkel"

# folgender Befehl zeigt mehr informationen
python3 abgeordnetenwatch-python/load_questions_answers.py --help
```

Das erzeugt eine Datei `data/079137_Angela_Merkel.csv` mit allen Fragen und Antworten der betreffenden Person.

### Parlament laden
Um alle Fragen und Antworten von allen Politikern aus einem Parlament zu holen, können Sie folgendes tun:

```sh
# Lade „bundestag“ mit 16 gleichzeitigen Anfragen
python3 abgeordnetenwatch-python/load_parliament_qa.py bundestag -t 16

# für weitere Optionen
python3 abgeordnetenwatch-python/load_parliament_qa.py --help
```

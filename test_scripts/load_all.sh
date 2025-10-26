#!/bin/bash

THREADS=8

load_parliament_qa bundestag --threads "$THREADS"
load_parliament_qa bremen --threads "$THREADS"
load_parliament_qa baden-württemberg --threads "$THREADS"
load_parliament_qa bayern --threads "$THREADS"
load_parliament_qa rheinland-pfalz --threads "$THREADS"
load_parliament_qa hessen --threads "$THREADS"
load_parliament_qa mecklenburg-vorpommern --threads "$THREADS"
load_parliament_qa saarland --threads "$THREADS"
load_parliament_qa sachsen --threads "$THREADS"
load_parliament_qa sachsen-anhalt --threads "$THREADS"
load_parliament_qa schleswig-holstein --threads "$THREADS"
load_parliament_qa niedersachsen --threads "$THREADS"
load_parliament_qa berlin --threads "$THREADS"
load_parliament_qa brandenburg --threads "$THREADS"
load_parliament_qa hamburg --threads "$THREADS"
load_parliament_qa nordrhein-westfalen --threads "$THREADS"
load_parliament_qa thüringen --threads "$THREADS"

#!/bin/bash

case "$1" in
	r)
		python3 src/main.py
		;;
	qa)
		shift
		python3 src/load_questions_answers.py "$@"
		;;
	t)
		python3 src/test.py
		;;
	*)
		echo "choose (r)un or (t)est"
		;;
esac

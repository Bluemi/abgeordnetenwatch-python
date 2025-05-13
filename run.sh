#!/bin/bash

case "$1" in
	r)
		python3 src/main.py
		;;
	qa)
		shift
		PYTHONPATH="$PWD/abgeordnetenwatch_python" python3 abgeordnetenwatch_python/cli/load_questions_answers.py "$@"
		;;
	p)
		shift
		PYTHONPATH="$PWD/abgeordnetenwatch_python" python3 abgeordnetenwatch_python/cli/load_parliament_qa.py "$@"
		;;
	t)
		python3 src/test.py
		;;
	*)
		echo "choose (r)un or (t)est"
		;;
esac

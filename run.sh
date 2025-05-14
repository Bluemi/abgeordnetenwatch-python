#!/bin/bash

case "$1" in
	r)
		shift
		PYTHONPATH="$PWD/abgeordnetenwatch_python" python3 "$@"
		;;
	qa)
		shift
		PYTHONPATH="$PWD/abgeordnetenwatch_python" python3 abgeordnetenwatch_python/cli/load_questions_answers.py "$@"
		;;
	p)
		shift
		PYTHONPATH="$PWD/abgeordnetenwatch_python" python3 abgeordnetenwatch_python/cli/load_parliament_qa.py "$@"
		;;
	*)
		echo "invalid option"
		;;
esac

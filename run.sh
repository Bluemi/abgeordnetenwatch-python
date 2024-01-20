#!/bin/bash

case "$1" in
	r)
		python3 src/main.py
		;;
	t)
		python3 src/test.py
		;;
	*)
		echo "choose (r)un or (t)est"
		;;
esac

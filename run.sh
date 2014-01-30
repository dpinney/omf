#!/usr/bin/env bash
touch log.txt
python omf.py 1>>log.txt 2>>log.txt &

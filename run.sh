#!/usr/bin/env bash
touch log.txt
python doeDemo.py 1>>log.txt 2>>log.txt &

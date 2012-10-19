#!/bin/python

''' Some utility data and functions. '''

def fileSlurp(fileName):
	with open(fileName,'r') as openFile:
		return openFile.read()

def main():
	# Tests go here.
	print fileSlurp('lib.py')

if __name__ == '__main__':
	main()
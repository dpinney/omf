#!/usr/bin/env python

def printNestDicts(nestedDicts, indentLevel=0):
	def printIndented(string, indentLevel):
		print ('\t' * indentLevel) + string
	for key in nestedDicts:
		value = nestedDicts[key]
		if type(value) is dict:
			printIndented(str(key) + ':', indentLevel)
			printNestDicts(value, indentLevel+1)
		else:
			outString = str(key) + ':' + str(value)
			if len(outString) > 60:
				printIndented(outString[0:60] + '...', indentLevel)
			else:
				printIndented(outString, indentLevel)

def main():
	'''Tests go here'''
	printNestDicts({'chicken':'magic',3:'chappies',65:{'gorgeous':56,'cheap':'level'}})

if __name__ == '__main__':
	main()
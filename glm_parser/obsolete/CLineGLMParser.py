#!/usr/bin/env python
# encoding: utf-8

"""

GLMParser-nonrec.py
Created by David Pinney on 2012-05-07.
"""

import sys
import getopt
import re
import GLMParserNonrec
import test

def main(argv=None):
	if argv is None:
		argv = sys.argv
	
	if len(argv) != 2:
		print 'This script takes one argument: the .glm to parse.'
	else:
		file = open(argv[1])
		glmData = file.read()
		dictList = GLMParserNonrec.parse(glmData)
		tests.tests(dictList)

if __name__ == "__main__":
	sys.exit(main())

#!/usr/bin/env python

input1 = '''
15 APRIL - BETA 1:
*55 Reporting: reliability studies (SAIDI, SAIFI, CAIDI, etc.). There is a GridlabD module for doing this.
*33 Schedule editor and schedule support in parser.
*10 Gridedit: code to add solar to feeders in a way similar to how we add houses.
*10 Import node positions from Milsoft.
*10 Platform: support for collectors on wind.
*10 Monetization to Tom Lovas's spec. Awaiting Tom/George input. Set deadline to March.
*40 Platform: JSON object store for all data objects.
*10 Platform: do an audit of all the libraries we have, clean up the interfaces (e.g. treeParser shouldn't read files for itself, its write methods should be renamed toString, etc.).
*40 Platform: server provisioning.
'''

input2 = '''
15 JUNE - GENERAL AVAILABILITY:
*40 Gridedit: Google Maps for grids with lat-lon data. Example with D3 at http://bl.ocks.org/1125458.
*05 Gridedit: Adding and deleting attributes on feeder objects. Lets us support GridlabD functionality without constantly upgrading our components... Not critical.
*10 Gridedit: drag box and/or ctrl+click to multiselect. See this convo.
*30 Gridedit: cut/copy/paste.
*40 Platform: write specs for all the interchange object models.
*40 Platform: Add server health admin page. What does it track? Page loads, RAM/disk/CPU, log display. Need daemon to record these things.
*10 Platform: sane logging system. Include flask.request.remote_addr!
*20 Reporting: load/gen curve report. Breakdown power by comm/res/ind. Also by Z/I/P.
'''

def printEstimate(input):
	split = input.splitlines()

	total = 0
	for line in split:
		if len(line) > 3 and line[0] == '*' and line[1:3].isdigit():
			# print line[1:3]
			total += int(line[1:3])

	print 'Total hours: ' + str(total)
	print 'Total workdays: ' + str(total/8.0)

printEstimate(input1)
printEstimate(input2)
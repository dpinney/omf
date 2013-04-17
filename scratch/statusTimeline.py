#!/usr/bin/env python

input1 = '''
15 APRIL - BETA 2:
*40 Studies: SAM integration.

15 JUNE - MIDINTERN:
*40 Import: bring in node positions from Milsoft.
*80 Platform: access control.
*20 Reporting: detect and explain Gridlab failures.
*05 Gridedit: Adding and deleting attributes on feeder objects. Lets us support GridlabD functionality without constantly upgrading our components.
*30 Platform: sane logging system. Include flask.request.remote_addr!
*60 Platform: PNNL branch integration.
*40 Studies: SCADA data study to compare power readings at the substation.
*60 Reporting: "Green" report.

31 JULY - LAUNCH
*99 Platform: determine where to host and what database to go with.
*30 Platform: get a domain.
*20 Platform: build a one-shot deployment pull script.
*40 Platform: get an nginx (and debian) config in place, demon strategy.
*40 Platform: first-time user instructions.
*40 Platform: landing/login page (see e.g. Outlook.com for inspiration).
*99 Platform: scaling to huge numbers of feeders/analyses.
*99 Platform: usability studies.
*99 Platform: beautification.
*99 Platform: round of deep bug fixing.
'''

input2 = '''
FAR FUTURE:
*40 Platform: write specs for all the interchange object models.
*40 Reporting: overloaded parts of the circuit.
*20 Reporting: load/gen curve report. Breakdown power by comm/res/ind. Also by Z/I/P.
*10 Platform: do an audit of all the libraries we have, clean up the interfaces (e.g. treeParser shouldn't read files for itself, its write methods should be renamed toString, etc.).
*20 Studies: Gridlab evcharger.
*40 Gridedit: Google Maps for grids with lat-lon data. Example with D3 at http://bl.ocks.org/1125458.
*10 Gridedit: drag box and/or ctrl+click to multiselect. See this convo.
*30 Gridedit: cut/copy/paste.
*40 Platform: get additional source databases (from openei.org) into the OMF.
*99 Studies: Gridlabd transmission system modeling.
*99 Gridedit: realtime Gridlab view mode. Alternatively a report that shows the feeder and allows stepping through time to show powerflow.
*99 Platform: look at a population of studies over a variable.
*99 Gridedit: giga-scale feeder visualization and editing.
*99 Platform: OMF running as a desktop app. Yes, definitely. What about synch'ing with the main crn-omf.saic.com?

LOW PRIORITY IDEAS:
*40 Platform: Add server health admin page. What does it track? Page loads, RAM/disk/CPU, log display. Need daemon to record these things. Let's go with a pre-built tool.
*20 Gridedit: investigate ESRI shapefile import. Could be very hard with a lack of object standards.
*05 Platform: iPad support. Hah! We're actually kind of close.
*04 Reporting: add density (std-devs) to the jiggle band chart. We can already get stddev from gridlab.
*02 Gridedit: make the selection table design better. No immediate benefit.
*03 Gridedit: do stroke-array lines to denote number of phases. See stroke-array in other note.
*10 Reporting: reveal data and allow interaction via the JS console. Will require rewriting all reports; isn't big improvement over rawData report.
*08 Gridedit: make the save/restore layout code cleaner and simpler by not saving/restoring links. Nontrivial change, no use case.
*15 Gridedit: we should pull configuration objects off into a separate menu somehow. Maybe. It's kind of inelegant.
*05 Studies: have analyses spawn subprocesses in a process group so we can kill with a single -9 and/or run in parallel. No use case, and process groups are UNIX-only.
*05 Studies: fix the runtime estimator and put it in the new analysis screen. No strong use case.
*05 Reporting: phase out aggCsv from reports.__util__ in favor of anaDataTree. No use case.
*05 Reporting: prettify study details in a table format. It's 98% good for now.
*88 Gridedit: figure out a way to get responsiveness while we're laying out a graph. Probably going to have to rewrite D3, which is nontrivial.
*99 Gridedit: thumb-nailing feeders? No strong use case.
*02 Platform: enable a refresh of the status on the homepage automagically via AJAX polling. Expensive in log space and computation. Revisit after logging redo.
*05 Platform: service architecture for job/resource/activity logging. See this for intermittent execution. Weak use case, logging could implement too.
*20 Platform: a depth-first parser. The execution would be clearer, it would be easier to debug and extend. Lots of hard work for not too much payoff.
*02 Gridedit: fix search so we can search modules and not just objects. Gross boolean syntax required.
*23 Gridedit: graphical schedule editor. Cron is good enough.
*10 Gridedit: better glyphs for houses, other components.
'''

def printEstimate(input):
	split = input.splitlines()

	total = 0
	for line in split:
		if len(line) > 3 and line[0] == '*' and line[1:3].isdigit():
			# print line[1:3]
			total += int(line[1:3])

	print 'Total hours: ', total
	print 'Total workdays: ', total/8.0
	print 'Total days: ', total/5.0
	print '--------------------------'

printEstimate(input1)
printEstimate(input2)
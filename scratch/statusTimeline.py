#!/usr/bin/env python

input = '''2xNEXT NEXT VERSION: DECENT M&V
*Make a demo video of synthCVR.
*10 Reporting: Tom's M+V report. What's on it?

3xNEXT VERSION
*03 Gridedit: User-editable names. Check to see we're not clobbering a name; rewire all the necessary froms/tos.
*03 Gridedit: Text labels. Use shadow css to make them readable and make sure they're on a (new?) highest layer.
*05 Gridedit: Adding and deleting attributes on feeder objects...
*10 Gridedit: drag box and/or ctrl+click to multiselect? See this convo.
*01 Gridedit: hide the skinny black bar when there's no selection. Use a css class.
*06 Reporting: implement house sample report? What's on it? Heating/lighting/appliance breakdown. Temperature timeseries. Set up via user-added recorders?
*04 Gridedit: visual indication of nodes with folded children.

4xNEXT VERSION:
*05 Analysis: Analysis editing (and duplication). Gonna need /newAnalysis to take a huge host of JSON arguments.
*05 Gridedit: implement a better zoom-to-fit.
*08 Gridedit: make the save/restore layout code cleaner and simpler by just saving/restoring node positions, weights and fixed stats.
*08 Reporting: refactor so a report can be described as [preProc(), postProc()], where postProc returns HTML and graphing instructions. See note reportingSpec.
*04 Gridedit: think about finding the subgraph along the longest lines...
*15 Gridedit: we should pull configuration objects off into a separate menu somehow.
*02 Analysis: Add a way to run the runtime estimator.
*40 Platform: How's that JSON object store going to work again?
*15 Gridedit: tree search.
*10 Analysis: have analyses spawn subprocesses in a process group so we can kill with a single -9 and/or run in parallel.
*01 Gridedit: enable preLayout() and display an interface while it works.
*40 Gridedit: Google Maps for grids with lat-lon data. Example with D3 at http://bl.ocks.org/1125458.
*30 Gridedit: cut/copy/paste'''

split = input.splitlines()

total = 0
for line in split:
	if len(line) > 3 and line[0] == '*' and line[1:3].isdigit():
		# print line[1:3]
		total += int(line[1:3])

print 'Total hours: ' + str(total)
print 'Total workdays: ' + str(total/8.0)
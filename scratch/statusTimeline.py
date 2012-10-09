#!/usr/bin/env python

input = '''
THIS WEEK: DECENT M&V
*10 Reporting: Tom's M+V report.
     * Implement a report that does as much of what he has already.
     * Set up a call to review what I've got, where he'd like to see improvements, and how we monetize.
* Do a great, monetized CVR run.
* Publish the CVR and solar results. At least a video.

2xNEXT VERSION - Frankly, nice to haves:
*06 Reporting: comparative grid viz reduced form report. Pie chart percentage comparison of unique nodes. Reduced form(s) of feeders.
*04 Reporting: ability to view the feeders in an analysis (the embedded ones, not the ones in the feeder store).
*10 Reporting/Gridedit: interface to display two+ different grids on top of each other, gray out the shared nodes, highlight the nodes unique to each feeder.
*02 Reporting: use a reasonable number of sig figs.
*06 Reporting: implement house sample report? What's on it? Heating/lighting/appliance breakdown. Temperature timeseries. Set up via user-added recorders or random sampling?
*04 Reporting: Break power usage out by systemLosses/
*05 Analysis: Analysis editing (and duplication). Gonna need /newAnalysis to take a huge host of JSON arguments.
*04 Reporting: add density (std-devs) to the jiggle band chart. We can already get stddev from gridlab. We can do a stacked area google chart.
*02 Analysis: Add a way to run the runtime estimator. Or have a new estimator based on stdout.txts.
*30 Gridedit: cut/copy/paste.
*10 Gridedit: drag box and/or ctrl+click to multiselect? See this convo.
*55 Reporting: reliability studies (CAIDA, SAIDA, etc.).
*05 Reporting: Doug's solar report.
*15 Gridedit: we should pull configuration objects off into a separate menu somehow.
*40 Platform: How's that JSON object store going to work again?
*08 Refactor: make the save/restore layout code cleaner and simpler by just saving/restoring node positions, weights and fixed stats. Also, integrate json caching with this.
*10 Analysis: have analyses spawn subprocesses in a process group so we can kill with a single -9 and/or run in parallel.
*15 Gridedit: tree search?
*05 Gridedit: Adding and deleting attributes on feeder objects. Enables advanced GridlabD functionality. Not critical.
*03 Refactor: folding code needs a review to make it cleaner.
'''

split = input.splitlines()

total = 0
for line in split:
	if len(line) > 3 and line[0] == '*' and line[1:3].isdigit():
		# print line[1:3]
		total += int(line[1:3])

print 'Total hours: ' + str(total)
print 'Total workdays: ' + str(total/8.0)
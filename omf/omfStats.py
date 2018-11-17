'''
Run this to generate stats about the OMF user base.
By david.pinney@nreca.coop and ian.george@nreca.coop in 2017.
Prereqs: a database file pulled from omf.coop, python, libraries listed below in the import statements (all pip installable).
Runtime: about 30 seconds.
OOO Think about what to do with the error log.
OOO Add a link to search tools: https://www.google.com/webmasters/tools/home?hl=en&authuser=0
OOO Add a link to AWS monitoring: https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Instances:InstanceId=i-054cb5c41369df768;sort=tag:Name
OOO Also throw in uptime monitoring: https://uptimerobot.com/dashboard#780640327
'''

import os
import csv
import json
from matplotlib import pyplot as plt
import time
from datetime import datetime
import collections
from geoip import geolite2
from iso3166 import countries
import zipfile

plt.style.use('ggplot')

def genModelDatabase(outPath):
	'''Translates all models on serer to .tsv file'''
	modelDir = os.path.join(os.getcwd(), 'data/Model')
	with open(outPath, 'wb') as statsFile:
		writer = csv.writer(statsFile, delimiter='\t', lineterminator='\n')
		writer.writerow(['Owner', 'Model Name', 'Type', 'Runtime (H:M:S)', 'Status', 'Created'])
		for owner in [x for x in os.listdir(modelDir) if os.path.isdir(x)]:
			ownerDir = os.path.join(modelDir, owner)
			for project in [x for x in os.listdir(ownerDir) if os.path.isdir(x)]:
				projectDir = os.path.join(ownerDir, project)
				with open((projectDir + '/allInputData.json')) as j:
					jData = json.load(j)
				j.close()
				created = jData['created'].split('.')[0]
				if 'runTime' in jData:
					writer.writerow([owner, project, jData['modelType'], jData['runTime'], created])
				else:
					writer.writerow([owner, project, jData['modelType'], '', created])

def genAllImages():
	'''Creates tsv database of models and images from log'''
	model_db_path = './scratch/modelDatabase.tsv'
	genModelDatabase(model_db_path)  # Overwrite is good.
	modelDatabaseStats(model_db_path, './static/model_db_stats.png')
	trafficLogStats('./omf.log', './static/traffic_log_stats.png')

def modelDatabaseStats(dataFilePath, outFilePath):
	# Last run:
	# #REPIC(time.strftime("%c"))  #OUTPUT: Sat Nov 17 02:39:05 2018
	# Import the data.
	models = []
	with open(dataFilePath, 'r') as inFile:
		reader = csv.DictReader(inFile, delimiter='\t')
		for row in reader:
			models.append(row)
	# Example of what the data structure looks like:
	#REPIC(models[1:3])  #OUTPUT: [{'Status': '2017-02-15 11:11:41', 'Created': None, 'Runtime (H:M:S)': '0:03:39', 'Model Name': 'Demo gridlabMulti scadaCalibration', 'Owner': 'public', 'Type': 'gridlabMulti'}, {'Status': '2014-07-30 11:23:46', 'Created': None, 'Runtime (H:M:S)': '0:00:37', 'Model Name': 'Demo Wind Olin Barre GH Wind', 'Owner': 'public', 'Type': 'gridlabMulti'}]
	# Model count:
	#REPIC(len(models))  #OUTPUT: 17
	# Note that this will undercount users because some users view but don't create models.
	users = set([x['Owner'] for x in models])
	# User count:
	#REPIC(len(users))  #OUTPUT: 2
	organizations = set([x.split('@')[-1] for x in users])
	# Organizations with one or more users:
	#REPIC(len(organizations))  #OUTPUT: 2
	# Counts per model:
	modelTypes = set([x['Type'] for x in models])
	modelCounts = {x: len([y for y in models if y['Type'] == x]) for x in modelTypes}
	#REPIC(modelCounts)  #OUTPUT: {'solarEngineering': 1, 'solarFinancial': 1, 'cvrStatic': 1, 'solarCashflow': 1, 'gridlabMulti': 7, 'solarSunda': 1, 'voltageDrop': 3, 'storagePeakShave': 1, 'pvWatts': 1}

	# Calculate users over time.
	def getYear(dateString):
		try:
			return dateString[0:4]
		except:
			return 'dateless'

	earliestDates = {x: min([getYear(y['Created']) for y in models if y['Owner'] == x]) for x in users}
	userDatePairs = zip(earliestDates.keys(), earliestDates.values())
	years = set(earliestDates.values())
	#REPIC(years)  #OUTPUT: set(['dateless'])
	yearUsers = {y: len([x for x in userDatePairs if x[1] == y]) for y in years}
	# HACK: some models missing dates.
	#yearUsers['2014'] += yearUsers['']; yearUsers.pop('')
	# HACK: estimate 2017 number based on July data.
	#yearUsers['2017'] = yearUsers['2017']*2
	# Sort it for nice plotting.
	yearUsers = collections.OrderedDict(sorted(yearUsers.items()))
	#REPIC(yearUsers)  #OUTPUT: OrderedDict([('dateless', 2)])
	# Plot users over time
	plt.figure(figsize=(12, 8))
	plt.subplot(2, 1, 1)
	xRanges2 = range(len(yearUsers.values()))
	plt.bar(xRanges2, yearUsers.values())
	ax = plt.gca()
	ax.set_xlim(-0.2, len(yearUsers.values()))
	ax = plt.gca()
	ax.set_title("New Users on omf.coop by Year")
	plt.xticks([x + 0.4 for x in xRanges2], yearUsers.keys())
	plt.subplots_adjust(bottom=0.2)
	# Plot the model counts.
	plt.subplot(2, 1, 2)
	xRanges = range(len(modelCounts.values()))
	plt.bar(xRanges, modelCounts.values())
	ax = plt.gca()
	ax.set_title("Count of Models on omf.coop by Type")
	ax.set_xlim(-0.2, len(modelCounts.values()))
	plt.xticks([x + 0.4 for x in xRanges], modelCounts.keys(), rotation='vertical')
	plt.subplots_adjust(bottom=0.2)
	plt.savefig(outFilePath)


def trafficLogStats(logsPath, outFilePath):
	# Read in a file containing the full access log.
	if logsPath.endswith('.zip'):
		# Support for reading zipped logs.
		zfile = zipfile.ZipFile(logsPath, 'r')
		fname = [x for x in zfile.namelist() if '/' not in x][0]
		zcontent = zfile.open(fname)
		lines = zcontent.readlines()
	else:
		# Support for plain text logs.
		logfile = open(logsPath, 'r')
		lines = logfile.readlines()
		logfile.close()
	# Create data structures for tracking metrics
	recordCount = collections.Counter()
	monthCount = collections.Counter()
	browserCount = collections.Counter()
	IPCount = collections.Counter()
	userCount = collections.Counter()
	users = set()  # Create set of users to prevent duplications.
	# Process the log file to generate hit and session counts.
	# Filter out lines containing these strings.
	for line in lines:
		# Skip any errors.
		if not line.startswith('INFO') or '* Running on' in line:
			continue
		# HACK: make werkzeug format match Apache's.
		comp = line.split(':')
		goodComps = comp[0] + ':' + comp[1]
		line = line.replace(goodComps + ':', goodComps + ' ')
		# Now split and define things.
		words = line.split()
		ip = geolite2.lookup(words[1])
		if ip is not None and ip.country is not None:
			if ip.country == 'XK':
				IPCount["Kosovo"] += 1
			else:
				nation = countries.get(ip.country)
				IPCount[nation.name] += 1
		if "GET" in words[6]:  # If this is a GET request...
			if "Chrome" in line:
				browserCount["Chrome"] += 1
			elif "Firefox" in line:
				browserCount["FireFox"] += 1
			elif "Safari" in line:
				browserCount["Safari"] += 1
			elif "Explorer" in line:
				browserCount["Internet Explorer"] += 1
			else:
				browserCount["Other"] += 1
			browserCount["Other"] += 1
			startIndex = line.index("[")
			endIndex = line.index("]")
			parsedLine = line[startIndex + 1:endIndex]  # Get date of access.
			if words[1] not in users:  # Is this is a unique viewer?
				recordCount[parsedLine[3:11]] += 1  # Add another user to the count.
				users.add(words[1])
			monthCount[parsedLine[3:11]] += 1  # No matter what, we update the monthly count.
			userCount[words[1]] += 1
	# Set up plotting:
	plt.figure(figsize=(15, 15))
	ggColors = [x['color'] for x in plt.rcParams['axes.prop_cycle']]
	# Session counts by month:
	log = collections.OrderedDict(sorted(recordCount.items(), key=lambda x: datetime.strptime(x[0], "%b/%Y")))
	plt.subplot(3, 1, 1)
	ax = plt.gca()
	ax.set_title('Session Count By Month. Total: ' + "{:,}".format(sum(log.values())))
	barRange = range(len(log))
	plt.bar(barRange, log.values(), align='center')
	plt.xticks(barRange, [x.replace('/', '\n') for x in log.keys()])
	plt.axis('tight')
	# Hit counts by month:
	log = collections.OrderedDict(sorted(monthCount.items(), key=lambda x: datetime.strptime(x[0], "%b/%Y")))
	plt.subplot(3, 1, 2)
	ax = plt.gca()
	ax.set_title('Hit Count By Month. Total: ' + "{:,}".format(sum(log.values())))
	barRange = range(len(log))
	plt.bar(barRange, log.values(), align='center')
	plt.xticks(barRange, [x.replace('/', '\n') for x in log.keys()])
	plt.axis('tight')
	# Plot the hits per user histogram:
	userElements = userCount.items()
	browserElements = browserCount.items()
	plt.subplot(3, 3, 7)
	userValues = list(pair[1] for pair in userElements)
	title = 'Histogram of Hits Per User'
	plt.title(title)
	plt.hist(userValues, bins=range(0, 50, 5))
	# Country hit counts:
	log = collections.OrderedDict(sorted(IPCount.items(), key=lambda x: x[1], reverse=True))
	countryTotal = str(len(log))
	# Just look at top 10 countries:
	for i, k in enumerate(log):
		if i > 10: del log[k]
	plt.subplot(3, 3, 8)
	ax = plt.gca()
	title = 'Hits by Country. Total Countries: ' + countryTotal
	ax.set_title(title)
	people = [x[0:14] for x in log.keys()]
	y_pos = range(len(people))
	performance = [x for x in log.values()]
	ax.barh(y_pos, performance, align='center')
	ax.set_yticks(y_pos)
	ax.set_yticklabels(people, fontsize=8)
	ax.invert_yaxis()  # labels read top-to-bottom
	# Plot of the number of hits by IP address:
	# u_label_list = list(pair[0] for pair in userElements)
	# IPCounts = filter(lambda x: x[1] >= 100, [(l, s) for l, s in zip(u_label_list, userValues)])
	# colors  = ('red', 'green', 'orange', 'cyan', 'brown', 'grey', 'blue', 'indigo', 'beige', 'yellow')
	# plt.pie(sorted(userValues, reverse=True), colors=colors)
	# plt.axis("equal")
	# plt.legend(loc=(-0.15, 0.05), labels=sorted(IPCounts, key = lambda x: x[1], reverse=True), shadow=True)
	# plt.savefig('USER HITS' + '.png')
	# plt.show()
	# plt.close()
	# def IPConvert(ip):
	# 	removePeriods = ''.join(ip.split('.'))
	# 	final = removePeriods.replace(':', '')
	# 	return int((''.join(ip.split('.')).replace(':','')))
	# Browser type breakdown:
	b_label_list = list(x[0] for x in browserElements if x[0] != 'Other')
	browserValues = list(int(x[1]) for x in browserElements if x[0] != 'Other')
	plt.subplot(3, 3, 9)
	plt.pie(sorted(browserValues, reverse=True), colors=ggColors)
	browserLabels = [(l, s) for l, s in zip(b_label_list, browserValues)]
	plt.legend(labels=sorted(browserLabels, key=lambda x: x[1], reverse=True), shadow=True)
	title = 'Browser Type Breakdown'
	plt.title(title)
	# Adjust and write out the image.
	plt.subplots_adjust(left=0.1, right=0.9)
	plt.savefig(outFilePath)

if __name__ == '__main__':
	genAllImages()
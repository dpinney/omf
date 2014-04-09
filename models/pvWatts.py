''' Powerflow results for one Gridlab instance. '''

import json, os, sys, tempfile, webbrowser, time, shutil, datetime, subprocess, datetime as dt
import multiprocessing
from os.path import join as pJoin
from jinja2 import Template
import __util__ as util

# Locational variables so we don't have to rely on OMF being in the system path.
_myDir = os.path.dirname(os.path.abspath(__file__))
_omfDir = os.path.dirname(_myDir)

# OMF imports
sys.path.append(_omfDir)
import feeder
from solvers import nrelsam

# Our HTML template for the interface:
with open(pJoin(_myDir,"pvWatts.html"),"r") as tempFile:
	template = Template(tempFile.read())

def renderTemplate(modelDir="", absolutePaths=False, datastoreNames={}):
	''' Render the model template to an HTML string.
	By default render a blank one for new input.
	If modelDir is valid, render results post-model-run.
	If absolutePaths, the HTML can be opened without a server. '''
	try:
		allInputData = open(pJoin(modelDir,"allInputData.json")).read()
	except IOError:
		allInputData = None
	try:
		allOutputData = open(pJoin(modelDir,"allOutputData.json")).read()
	except IOError:
		allOutputData = None
	if absolutePaths:
		# Parent of current folder.
		pathPrefix = _omfDir
	else:
		pathPrefix = ""
	return template.render(allInputData=allInputData,
		allOutputData=allOutputData, pathPrefix=pathPrefix,
		datastoreNames=datastoreNames)

def renderAndShow(modelDir="", datastoreNames={}):
	''' Render and open a template (blank or with output) in a local browser. '''
	with tempfile.NamedTemporaryFile() as temp:
		temp.write(renderTemplate(modelDir=modelDir, absolutePaths=True))
		temp.flush()
		os.rename(temp.name, temp.name + '.html')
		fullArg = 'file://' + temp.name + '.html'
		webbrowser.open(fullArg)
		# It's going to SPACE! Could you give it a SECOND to get back from SPACE?!
		time.sleep(1)

def create(parentDirectory, inData):
	''' Make a directory for the model to live in, and put the input data into it. '''
	modelDir = pJoin(parentDirectory,inData["user"],inData["modelName"])
	os.mkdir(modelDir)
	inData["created"] = str(datetime.datetime.now())
	with open(pJoin(modelDir,"allInputData.json"),"w") as inputFile:
		json.dump(inData, inputFile, indent=4)
	# Copy datastore data.
	shutil.copy(pJoin(_omfDir,"data","Climate",inData["climateName"] + ".tmy2"),
		pJoin(modelDir,"climate.tmy2"))

def run(modelDir):
	''' Run the model in its directory. '''
	try:
		# Create a running directory and fill it.
		studyPath = 'running/' + self.analysisName + '---' + self.name + '___' + str(datetime.now()).replace(':','_') + '/'
		os.makedirs(studyPath)
		# Write attachments and glm.
		attachments = self.inputJson['attachments']
		for attach in attachments:
			with open (studyPath + attach,'w') as attachFile:
				attachFile.write(attachments[attach])
		# setup data structures
		ssc = solvers.nrelsam.SSCAPI()
		dat = ssc.ssc_data_create()
		# required inputs
		ssc.ssc_data_set_string(dat, "file_name", studyPath + "/climate.tmy2")
		ssc.ssc_data_set_number(dat, "system_size", float(self.inputJson['systemSize']))
		ssc.ssc_data_set_number(dat, "derate", float(self.inputJson['derate']))
		ssc.ssc_data_set_number(dat, "track_mode", float(self.inputJson['trackingMode']))
		ssc.ssc_data_set_number(dat, "azimuth", float(self.inputJson['azimuth']))
		# default inputs exposed
		ssc.ssc_data_set_number(dat, 'rotlim', float(self.inputJson['rotlim']))
		ssc.ssc_data_set_number(dat, 't_noct', float(self.inputJson['t_noct']))
		ssc.ssc_data_set_number(dat, 't_ref', float(self.inputJson['t_ref']))
		ssc.ssc_data_set_number(dat, 'gamma', float(self.inputJson['gamma']))
		ssc.ssc_data_set_number(dat, 'inv_eff', float(self.inputJson['inv_eff']))
		ssc.ssc_data_set_number(dat, 'fd', float(self.inputJson['fd']))
		ssc.ssc_data_set_number(dat, 'i_ref', float(self.inputJson['i_ref']))
		ssc.ssc_data_set_number(dat, 'poa_cutin', float(self.inputJson['poa_cutin']))
		ssc.ssc_data_set_number(dat, 'w_stow', float(self.inputJson['w_stow']))
		# complicated optional inputs
		ssc.ssc_data_set_number(dat, 'tilt_eq_lat', 1)
		# ssc.ssc_data_set_array(dat, 'shading_hourly', ...) 	# Hourly beam shading factors
		# ssc.ssc_data_set_matrix(dat, 'shading_mxh', ...) 		# Month x Hour beam shading factors
		# ssc.ssc_data_set_matrix(dat, 'shading_azal', ...) 	# Azimuth x altitude beam shading factors
		# ssc.ssc_data_set_number(dat, 'shading_diff', ...) 	# Diffuse shading factor
		# ssc.ssc_data_set_number(dat, 'enable_user_poa', ...)	# Enable user-defined POA irradiance input = 0 or 1
		# ssc.ssc_data_set_array(dat, 'user_poa', ...) 			# User-defined POA irradiance in W/m2
		# ssc.ssc_data_set_number(dat, 'tilt', 999)

		# run PV system simulation
		mod = ssc.ssc_module_create("pvwattsv1")
		ssc.ssc_module_exec(mod, dat)

		# MD calc.
		if self.simLengthUnits == 'days':
			startDateTime = self.simStartDate
		else:
			startDateTime = self.simStartDate + ' 00:00:00 PDT'

		# Extract data.
		# Timestamps.
		outData = {}
		outData['timeStamps'] = [startDateTime for x in range(self.simLength)]
		# Geodata.
		outData['city'] = ssc.ssc_data_get_string(dat, 'city')
		outData['state'] = ssc.ssc_data_get_string(dat, 'state')
		outData['lat'] = ssc.ssc_data_get_number(dat, 'lat')
		outData['lon'] = ssc.ssc_data_get_number(dat, 'lon')
		outData['elev'] = ssc.ssc_data_get_number(dat, 'elev')
		# Weather
		outData['climate'] = {}
		outData['climate']['irrad'] = _aggData('dn', util.avg)
		outData['climate']['diffIrrad'] = _aggData('df', util.avg)
		outData['climate']['temp'] = _aggData('tamb', util.avg)
		outData['climate']['cellTemp'] = _aggData('tcell', util.avg)
		outData['climate']['wind'] = _aggData('wspd', util.avg)
		# Power generation.
		outData['Consumption'] = {}
		outData['Consumption']['Power'] = [-1*x for x in _aggData('ac', util.avg)]
		outData['Consumption']['Losses'] = [0 for x in _aggData('ac', util.avg)]
		outData['Consumption']['DG'] = _aggData('ac', util.avg)
		# Stdout/stderr.
		outData['stdout'] = 'Success'
		outData['stderr'] = ''
		# componentNames.
		outData['componentNames'] = []
		shutil.rmtree(studyPath)
		self.outputJson = outData
	except:
		self.outputJson = {'stdout':'Failure'}

def _aggData(key, aggFun):
	''' Function to aggregate output if we need something other than hour level. '''
	u = self.simStartDate
	dt = datetime(int(u[0:4]),int(u[5:7]),int(u[8:10]))
	v = dt.isocalendar()
	initHour = int(8760*(v[1]+v[2]/7)/52.0)
	fullData = ssc.ssc_data_get_array(dat, key)
	if self.simLengthUnits == 'days':
		multiplier = 24
	else:
		multiplier = 1
	hourData = [fullData[(initHour+i)%8760] for i in xrange(self.simLength*multiplier)]
	if self.simLengthUnits == 'minutes':
		pass
	elif self.simLengthUnits == 'hours':
		return hourData
	elif self.simLengthUnits == 'days':
		split = [hourData[x:x+24] for x in xrange(self.simLength)]
		return map(aggFun, split)

def cancel(modelDir):
	''' PV Watts runs so fast it's pointless to cancel a run. '''
	pass

def _tests():
	# No-input template.
	renderAndShow()

if __name__ == '__main__':
	_tests()
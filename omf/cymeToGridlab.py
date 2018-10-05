'''
Created on Nov 19, 2013

@author: fish334

PREREQS!!!!!! sudo apt-get install mdbtools libmdbodbc1

This script converts a CYME feeder model database to an OMF feeder tree dictionary object. The out put is similar to that produced by milToGridlab.py

An example of how to call the script is shown below:
	import convert_cyme_model
	feederTree = convert_cyme_model.convertCymeModel(db_network, db_equipment, id_feeder, conductors)

where:

db_network is the full path to the CYME network .mdb database file.
db_equipment is the full path to the CYME equipment .mdb database file.
id_feeder is a string of the NetworkId associated with the particular feeder.
conductors is the full path to a .csv file containing conductor information for underground concentric neutral and tape shield cables used in the CYME model.

Note that db_network and db_equipment can be the same file is both network and equipment databases were exported to one .mdb file from CYME.
'''

import feeder, csv, random, math, copy, subprocess, locale, tempfile
from os.path import join as pJoin
import warnings
from StringIO import StringIO
import sys, os, json, traceback, shutil
from solvers import gridlabd
from pathlib import Path
import matplotlib
matplotlib.pyplot.switch_backend('Agg')
from matplotlib import pyplot as plt
import numpy as np
from numpy.linalg import inv
import platform

m2ft = 1.0/0.3048 # Conversion factor for meters to feet

class Map(dict):
	"""
	Example:
	m = Map({'first_name': 'Eduardo'}, last_name='Pool', age=24, sports=['Soccer'])
	"""
	def __init__(self, *args, **kwargs):
		super(Map, self).__init__(*args, **kwargs)
		for arg in args:
			if isinstance(arg, dict):
				for k, v in arg.iteritems():
					self[k] = v
		if kwargs:
			for k, v in kwargs.iteritems():
				self[k] = v

	def __getattr__(self, attr):
		return self.get(attr)

	def __setattr__(self, key, value):
		self.__setitem__(key, value)

	def __setitem__(self, key, value):
		super(Map, self).__setitem__(key, value)
		self.__dict__.update({key: value})

	def __delattr__(self, item):
		self.__delitem__(item)

	def __delitem__(self, key):
		super(Map, self).__delitem__(key)
		del self.__dict__[key]

def _csvDump(database_file, modelDir):
	# Get the list of table names with "mdb-tables"
	if platform.system() == 'Linux' or platform.system() == 'Darwin':
		table_names = subprocess.Popen(["mdb-tables", "-1", database_file],
			stdout=subprocess.PIPE).communicate()[0]
		tables = table_names.split('\n')
		if not os.path.isdir((pJoin(modelDir,'cymeCsvDump'))):
			os.makedirs((pJoin(modelDir,'cymeCsvDump')))
		# Dump each table as a CSV file using "mdb-export",
		# converting " " in table names to "_" for the CSV filenames.
		for table in tables:
			if table != '':
				filename = table.replace(" ","_") + ".csv"
				file = open(pJoin(modelDir,'cymeCsvDump',filename), 'w+')
				contents = subprocess.Popen(["mdb-export", database_file, table],
					stdout=subprocess.PIPE).communicate()[0]
				file.write(contents)
				file.close()
	elif platform.system() == 'Windows':
		#The following code uses mdb-tables in Windows 10, but requires the creators update and ubuntu
		#One big problem:  after this function dumps the csv files, python crashes. So I have to run this routine twice.
		originaldir = os.getcwd()#bash command below wouldn't work if I appended path to database_file
		os.chdir(modelDir)
		database_file = database_file.split('\\')[-1]
		table_names = subprocess.Popen(["bash", "-c", "mdb-tables -1 " + database_file], stdout=subprocess.PIPE).communicate()[0]
		tables = table_names.split('\n')
		if not os.path.isdir((pJoin(modelDir,'cymeCsvDump'))):
			os.makedirs((pJoin(modelDir,'cymeCsvDump')))
		# Dump each table as a CSV file using "mdb-export",
		# converting " " in table names to "_" for the CSV filenames.
		for table in tables:
			if table != '':
				filename = table.replace(" ","_") + ".csv"
				file = open(pJoin(modelDir,'cymeCsvDump',filename), 'w+')
				contents = subprocess.Popen(["bash", "-c", "mdb-export " + database_file + " " +table],
					stdout=subprocess.PIPE).communicate()[0]
				file.write(contents)
				file.close()
		os.chdir(originaldir)

def _findNetworkId(csvFile):
	csvDict = csv.DictReader(open(csvFile,'r'))
	networks = []
	for row in csvDict:
		networks.append(row['NetworkId'])
	# HACK: For multi-source networks (Titanium), select the second source
	# Need to find a way to do this better
	if len(networks)>1:
		return networks[1]
	else:
	# If single source network, select the only source
		return networks[0]

def _isfloat(value):
  'Helper function for _fixName.'
  try:
    float(value)
    return True
  except:
    return False

def _fixName(name):
	'Function that replaces characters not allowed in name with _'
	badChar = [' ', '-', '\\', '//', '/', ':', '.', "'\'", '&']
	for char in badChar:
		name = name.replace(char, '_')
	#jfk.  Don't allow names that start with a number
	if _isfloat(name[0]):
		name = 'x'+name
	return name

def _convertPhase(int_phase):
	'Function that converts a number to a phase'
	if int_phase == 1:
		phase = 'AN'
	elif int_phase == 2:
		phase = 'BN'
	elif int_phase == 3:
		phase = 'CN'
	elif int_phase == 4:
		phase = 'ABN'
	elif int_phase == 5:
		phase = 'ACN'
	elif int_phase == 6:
		phase = 'BCN'
	elif int_phase == 7:
		phase = 'ABCN'
	else:
		phase = None
	return phase

def _convertRegulatorPhase(int_phase):
	'''Function that converts a number to a phase'''
	if int_phase == 1:
		phase = 'A'
	elif int_phase == 2:
		phase = 'B'
	elif int_phase == 3:
		phase = 'C'
	elif int_phase == 4:
		phase = 'AB'
	elif int_phase == 5:
		phase = 'AC'
	elif int_phase == 6:
		phase = 'BC'
	elif int_phase == 7:
		phase = 'ABC'
	else:
		phase = None           
	return phase

def _convertLoadClass(class_from_db):
	'''# Function the converts a load classification string to a number'''
	classes = {}
	classes['Residential1'] = 0
	classes['Residential2'] = 1
	classes['Residential3'] = 2
	classes['Residential4'] = 3
	classes['Residential5'] = 4
	classes['Residential6'] = 5
	classes['Commercial1'] = 6
	classes['Commercial2'] = 7
	classes['Commercial3'] = 8
	if class_from_db in classes.keys():
		return classes[class_from_db]
	else:
		return None

def _csvToArray(csvFileName):
	''' Simple .csv data ingester. '''
	with open(csvFileName,'r') as csvFile:
		csvReader = csv.reader(csvFile)
		outArray = []
		for row in csvReader:
			outArray += [row]
		return outArray

def _csvToDictList(csvFileName,feederId):
	included_columns = []
	header = []
	mapped  = []
	deleteRows = []
	content = []
	sourceFile = csv.reader(open(csvFileName))
	header = sourceFile.next()
	csvDict = csv.DictReader(open(csvFileName,'r'))
	for row in csvDict:
		# Equipment files, all equipment gets added
		if 'NetworkId' not in header:
			mapped.append(Map(row))
		elif row['NetworkId'] == feederId:
			mapped.append(Map(row))
	return mapped

def checkMissingNodes(nodes, sectionDevices, objectList, feederId, modelDir, cymsection):
	dbNodes = []
	MISSINGNO = {'name': None}
	nodesNotMake = {}
	missingNodes = []
	glmObjs = []
	objNotMiss =[]
	toNodesMissing = []
	sectionObjects = []
	otherObjects = []
	nonMissNodes = []
	nodesLen = len(nodes)
	# Make missingNodesReport.txt
	missingNodesReport = pJoin(modelDir,'missingNodesReport.txt')
	with open(missingNodesReport,'w') as inFile:
		inFile.write('Missing nodes report for ' +  feederId  + '\nList of missing nodes:\n')
	node_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMNODE.csv"),feederId)
	# Nodes in mdb are compared with nodes in glm and missing nodes is populated with those missing
	for row in node_db:
		dbNodes.append(_fixName(row['NodeId']))
		if _fixName(row['NodeId']) not in nodes:
			nodesNotMake[_fixName(row['NodeId'])] = copy.deepcopy(MISSINGNO)
			nodesNotMake[_fixName(row['NodeId'])]['name'] =  _fixName(row['NodeId'])
			missingNodes.append(_fixName(row['NodeId']))
			with open(missingNodesReport,'a') as inFile:
				inFile.write(_fixName(row['NodeId'])+'\n')
	# All objects in glm are put in a list
	for row in objectList:
		for key in row.keys():
			glmObjs.append(key)
	# Comparing missing nodes names to names of other glm objects to see if they are not nodes but other objects
	# For Titanium these are batteries, diesel dg
	with open(missingNodesReport,'a') as inFile:
		inFile.write('Comparing the names of the missing nodes to the names of other objects in the .glm:\n')
	for row in missingNodes:
		if row in glmObjs:
			with open(missingNodesReport,'a') as inFile:
				inFile.write(row+' was found as an existing object in the .glm. Removing it from the list of missing nodes...\n')
			objNotMiss.append(row)
	# remove above objects from missing nodes list
	for row in objNotMiss:
		missingNodes.remove(row)
	with open(missingNodesReport,'a') as inFile:
				inFile.write('Updated list of missing nodes:\n')
	for row in missingNodes:
		with open(missingNodesReport,'a') as inFile:
			inFile.write(row+'\n')
	# check cymsection for the missing device and its corresponding device
	with open(missingNodesReport,'a') as inFile:
		inFile.write('Some nodes get absorbed into the objects that they lead to, checking for this situation now...\n')
	for row in cymsection:
		for missNode in missingNodes:
			if cymsection[row]['to'] == missNode:
				sectionId = cymsection[row]['name']
				with open(missingNodesReport,'a') as inFile:
					inFile.write('The missing node '+missNode+ ' is a part of the section '+sectionId+'\n')
				for dev in sectionDevices:
					if sectionDevices[dev]['section_name'] == sectionId:
						sectionObjects.append(sectionDevices[dev]['name'])
						with open(missingNodesReport,'a') as inFile:
							inFile.write('This section corresponds to the device '+ sectionDevices[dev]['name']+ '\n')
	# check to see if that device is in the glm
	with open(missingNodesReport,'a') as inFile:
		inFile.write('Comparing those devices to objects that already exist in the .glm:\n')
	for row in sectionObjects:
		for obj in glmObjs:
			if row in obj and 'config' not in obj and '_' not in obj:
				if row not in otherObjects:
					otherObjects.append(row)
					with open(missingNodesReport,'a') as inFile:
						inFile.write(row+' was found as the existing object ' +obj+' in the .glm. Removing its parent node from the list of missing nodes...\n')
	# Removing nodes with devices in the glm from this missing nodes list
	for row in otherObjects:
		nonMissNodes.append(cymsection[sectionDevices[row]['section_name']]['to'])
	for row in nonMissNodes:
		missingNodes.remove(row)
	with open(missingNodesReport,'a') as inFile:
				inFile.write('Updated list of missing nodes:\n')
	for row in missingNodes:
		with open(missingNodesReport,'a') as inFile:
			inFile.write(row+'\n')

def _readCymeSource(feederId, type, modelDir):
	'''store information for the swing bus'''
	cymsource = {}                          # Stores information found in CYMSOURCE or CYMEQUIVALENTSOURCE in the network database    
	if (type==1):
		CYMSOURCE = { 'name' : None,            # information structure for each object found in CYMSOURCE
								'bustype' : 'SWING',
								'nominal_voltage' : None,
								'phases' : None}
		# Check to see if the network database contains models for more than one database and if we chose a valid feeder_id to convert
		feeder_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMSOURCE.csv"),feederId)
	elif (type==2):
		CYMEQUIVALENTSOURCE = { 'name' : None,            # information structure for each object found in CYMEQUIVALENTSOURCE
								'bustype' : 'SWING',
								'nominal_voltage' : None,
								'phases' : None}
		# Check to see if the network database contains models for more than one database and if we chose a valid feeder_id to convert
		# feeder_db = networkDatabase.execute("SELECT NodeId, OperatingVoltage1 FROM CYMEQUIVALENTSOURCE").fetchall()
		feeder_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMEQUIVALENTSOURCE.csv"),feederId)
		# feeder_db_net =  networkDatabase.execute("SELECT NetworkId FROM CYMNETWORK").fetchall()   
		feeder_db_net =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMNETWORK.csv"),feederId)
		if (feeder_db_net == None): 
			raise RuntimeError("No source node was found in CYMSOURCE: {:s}.\n".format(feederId))            
	if feeder_db == None:
		raise RuntimeError("No source node was found in CYMSOURCE: {:s}.\n".format(feederId))
	else:            
		try: 
			print "NetworkId", feeder_db_net 
		except:
			pass                 
	'''mj debug'''
	if feederId == None:
		'''mj debug'''
		print "NO FEEDER ID\n" 
		if len(feeder_db) >= 1:
			if len(feeder_db) == 1:
				try:
					for row in feeder_db:
						feeder_id = row.NetworkId
						cymsource[_fixName(row.NodeId)] = copy.deepcopy(CYMSOURCE)
						cymsource[_fixName(row.NodeId)]['name'] = _fixName(row.NodeId)
						cymsource[_fixName(row.NodeId)]['nominal_voltage'] = str(float(row.DesiredVoltage)*1000.0/math.sqrt(3))
				except:
					for row in feeder_db_net:
						feeder_id = row.NetworkId
						cymsource[_fixName(row.NodeId)] = copy.deepcopy(CYMEQUIVALENTOURCE)
						cymsource[_fixName(row.NodeId)]['name'] = _fixName(row.NodeId)
						cymsource[_fixName(row.NodeId)]['nominal_voltage'] = str(float(row.OperatingVoltage1)*1000.0/math.sqrt(3))                        
			else:
				raise RuntimeError("The was no feeder id given and the network database contians more than one feeder. Please specify a feeder id to extract.")
	else:
		'''mj debug'''
		print "FEEDER ID", feederId 
		feederIds = []
		if (type==1):
			for row in feeder_db:
				feederIds.append(row.NetworkId) 
			if feederId not in feederIds:
				raise RuntimeError("The feeder id provided is not in the network database. Please specify a valid feeder id to extract.")
			for row in feeder_db:
				if row.NetworkId == feederId:
					feeder_id = feederId
					cymsource[_fixName(row.NodeId)] = copy.deepcopy(CYMSOURCE)
					cymsource[_fixName(row.NodeId)]['name'] = _fixName(row.NodeId)
					cymsource[_fixName(row.NodeId)]['nominal_voltage'] = str(float(row.DesiredVoltage)*1000.0/math.sqrt(3))
					swingBus = _fixName(row.NodeId)     
		elif (type==2):
			for row in feeder_db_net:
				feederIds.append(row.NetworkId)  
			if feederId not in feederIds:
				raise RuntimeError("The feeder id provided is not in the network database. Please specify a valid feeder id to extract.")
			for row in feeder_db_net:             
				if row.NetworkId == feederId:
					feeder_id = feederId
			feederId_equivalent = "SOURCE_" + feeder_id
			for row in feeder_db:
				if row.NodeId in feederId_equivalent: #jfk.  logic was backwards.
					feeder_id = feederId
					cymsource[_fixName(row.NodeId)] = copy.deepcopy(CYMEQUIVALENTSOURCE)
					cymsource[_fixName(row.NodeId)]['name'] = _fixName(row.NodeId)
					#jfk. Differentiating between nominal voltage and voltage setpoint at the source.  Otherwise, per unit calcs get messy later.  Also, more accurate for capacitors.
					cymsource[_fixName(row.NodeId)]['nominal_voltage'] = str(float(row.KVLL)*1000.0/math.sqrt(3)) #jfk.
					cymsource[_fixName(row.NodeId)]['source_voltage'] = str(float(row.OperatingVoltage1)*1000.0) #jfk
					swingBus = _fixName(row.NodeId)
	return cymsource, feeder_id, swingBus

def _readCymeNode(feederId, modelDir):
	'''store lat/lon information on nodes'''
	# Helper for lat/lon conversion.
	x_list = []
	y_list = []
	x_pixel_range = 1200
	y_pixel_range = 800
	cymnode = {}
	CYMNODE = {'name' : None,
							'latitude' : None,
							'longitude' : None}
	# node_db = networkDatabase.execute("SELECT NodeId, X, Y FROM CYMNODE WHERE NetworkId = '{:s}'".format(feederId)).fetchall()
	node_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMNODE.csv"),feederId)
	if len(node_db) == 0:
		warnings.warn("No information node locations were found in CYMNODE for feeder id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in node_db:
			x_list.append(row.X)
			y_list.append(row.Y)
		xmax = float(max(x_list))
		xmin = float(min(x_list))
		ymax = float(max(y_list))
		ymin = float(min(y_list))
		try:
			x_scale = x_pixel_range / (xmax-xmin)
			x_b = -x_scale * xmin
			y_scale = y_pixel_range / (ymax-ymin)
			y_b = -y_scale * ymin
		except:
			x_scale,x_b,y_scale,y_b = (0,0,0,0)
		for row in node_db:
			row.NodeId = _fixName(row.NodeId)
			if row.NodeId not in cymnode.keys():
				cymnode[row.NodeId] = copy.deepcopy(CYMNODE)
				cymnode[row.NodeId]['name'] = row.NodeId
				cymnode[row.NodeId]['latitude'] = str(x_scale * float(row.X) + x_b)
				cymnode[row.NodeId]['longitude'] = str(800 -(y_scale * float(row.Y) + y_b)) 
	return cymnode, x_scale, y_scale
	
def _readCymeOverheadByPhase(feederId, modelDir):
	'''store information from CYMOVERHEADBYPHASE'''
	cymoverheadbyphase = {}     # Stores information found in CYMOVERHEADBYPHASE in the network database
	overheadLineConfiguration = {}
	olc = {}
	uniqueSpacing = []
	overheadConductors = []     # Stores the unique conductor equipment Ids
	CYMOVERHEADBYPHASE = { 'name' : None,       # Information structure for each object found in CYMOVERHEADBYPHASE
						  'length' : None,
						  'configuration' : None}
	# overheadbyphase_db = networkDatabase.execute("SELECT DeviceNumber, PhaseConductorIdA, PhaseConductorIdB, PhaseConductorIdC, NeutralConductorId, ConductorSpacingId, Length FROM CYMOVERHEADBYPHASE WHERE NetworkId = '{:s}'".format(feederId)).fetchall()
	overheadbyphase_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMOVERHEADBYPHASE.csv"),feederId)
	if len(overheadbyphase_db) == 0:
		warnings.warn("No information on phase conductors, spacing, and lengths were found in CYMOVERHEADBYPHASE for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	else:
		# Add all phase conductors to the line configuration dictionary.
		for row in overheadbyphase_db:
			row.DeviceNumber = _fixName(row.DeviceNumber)
			if row.DeviceNumber not in cymoverheadbyphase.keys():
				cymoverheadbyphase[row.DeviceNumber] = copy.deepcopy(CYMOVERHEADBYPHASE)
				cymoverheadbyphase[row.DeviceNumber]['name'] = row.DeviceNumber
				if row.PhaseConductorIdA != 'NONE':
					overheadLineConfiguration['conductor_A'] = _fixName(row.PhaseConductorIdA)
					if _fixName(row.PhaseConductorIdA) not in overheadConductors:
						overheadConductors.append(_fixName(row.PhaseConductorIdA))
				if row.PhaseConductorIdB != 'NONE':
					overheadLineConfiguration['conductor_B'] = _fixName(row.PhaseConductorIdB)
					if _fixName(row.PhaseConductorIdB) not in overheadConductors:
						overheadConductors.append(_fixName(row.PhaseConductorIdB))
				if row.PhaseConductorIdC != 'NONE':
					overheadLineConfiguration['conductor_C'] = _fixName(row.PhaseConductorIdC)
					if _fixName(row.PhaseConductorIdC) not in overheadConductors:
						overheadConductors.append(_fixName(row.PhaseConductorIdC))
				if row.NeutralConductorId != 'NONE':
					overheadLineConfiguration['conductor_N'] = _fixName(row.NeutralConductorId)
					if row.NeutralConductorId != 'NONE' and _fixName(row.NeutralConductorId) not in overheadConductors:
						overheadConductors.append(_fixName(row.NeutralConductorId))
				overheadLineConfiguration['spacing'] = _fixName(row.ConductorSpacingId)
				if _fixName(row.ConductorSpacingId) not in uniqueSpacing:
					uniqueSpacing.append(_fixName(row.ConductorSpacingId))           
				cymoverheadbyphase[row.DeviceNumber]['length'] = float(row.Length)*m2ft
				if cymoverheadbyphase[row.DeviceNumber]['length'] == 0.0:
					cymoverheadbyphase[row.DeviceNumber]['length'] = 1.0
				if len(olc) == 0:
					olc['olc0'] = copy.deepcopy(overheadLineConfiguration)
					cymoverheadbyphase[row.DeviceNumber]['configuration'] = 'olc0'
				else:
					for key in olc.keys():
						if overheadLineConfiguration == olc[key]:
							cymoverheadbyphase[row.DeviceNumber]['configuration'] = key
					if cymoverheadbyphase[row.DeviceNumber]['configuration'] == None:
						key = 'olc' + str(len(olc))
						olc[key] = copy.deepcopy(overheadLineConfiguration)
						cymoverheadbyphase[row.DeviceNumber]['configuration'] = key
	return overheadConductors, cymoverheadbyphase, olc, uniqueSpacing

def _readCymeUndergroundLine(feederId, modelDir):
	'''store information from CYMUNDERGROUNDLINE'''
	cymundergroundline = {}                         # Stores information found in CYMUNDERGOUNDLINE in the network database
	undergroundConductors = []  # Stores the unique underground conductor equipment Ids
	CYMUNDERGROUNDLINE = { 'name' : None,           # Information structure for each object found in CYMUNDERGROUNDLINE
						   'length' : None,
						   'cable_id': None}
	# ug_line_db = networkDatabase.execute("SELECT DeviceNumber, CableId, Length FROM CYMUNDERGROUNDLINE WHERE NetworkId = '{:s}'".format(feederId)).fetchall()
	ug_line_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMUNDERGROUNDLINE.csv"),feederId)
	if len(ug_line_db) == 0:
		warnings.warn("No underground_line objects were found in CYMUNDERGROUNDLINE for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in ug_line_db:
			row.DeviceNumber = _fixName(row.DeviceNumber)
			if row.DeviceNumber not in cymundergroundline.keys():
				cymundergroundline[row.DeviceNumber] = copy.deepcopy(CYMUNDERGROUNDLINE)
				cymundergroundline[row.DeviceNumber]['name'] = _fixName(row.DeviceNumber)  
				cymundergroundline[row.DeviceNumber]['cable_id'] = _fixName(row.CableId)
				cymundergroundline[row.DeviceNumber]['length'] = float(row.Length)*m2ft
				if cymundergroundline[row.DeviceNumber]['length'] == 0.0:
					cymundergroundline[row.DeviceNumber]['length'] = 1.0
				if _fixName(row.CableId) not in undergroundConductors:
					undergroundConductors.append(_fixName(row.CableId))
	return undergroundConductors, cymundergroundline

def _readCymeOverheadLineUnbalanced(feederId, modelDir):
	'''store information from CYMOVERHEADLINEUNBALANCED'''
	cymoverheadlineunbalanced = {}                         # Stores information found in CYMOVERHEADLINEUNBALANCED in the network database
	OhUbConductors = []  # Stores the unique underground conductor equipment Ids
	CYMOVERHEADLINEUNBALANCED = { 'name' : None,           # Information structure for each object found in CYMOVERHEADLINEUNBALANCED
						   'length' : None,
						   'configuration': None}
	# ug_line_db = networkDatabase.execute("SELECT DeviceNumber, LineId, Length FROM CYMOVERHEADLINEUNBALANCED WHERE NetworkId = '{:s}'".format(feederId)).fetchall()
	ug_line_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMOVERHEADLINEUNBALANCED.csv"),feederId)
	if len(ug_line_db) == 0:
		warnings.warn("No underground_line objects were found in CYMOVERHEADLINEUNBALANCED for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in ug_line_db:
			row.DeviceNumber = _fixName(row.DeviceNumber)
			if row.DeviceNumber not in cymoverheadlineunbalanced.keys():
				cymoverheadlineunbalanced[row.DeviceNumber] = copy.deepcopy(CYMOVERHEADLINEUNBALANCED)
				cymoverheadlineunbalanced[row.DeviceNumber]['name'] = _fixName(row.DeviceNumber)  
				cymoverheadlineunbalanced[row.DeviceNumber]['configuration'] = _fixName(row.LineId)
				cymoverheadlineunbalanced[row.DeviceNumber]['length'] = float(row.Length)*m2ft
				if cymoverheadlineunbalanced[row.DeviceNumber]['length'] == 0.0:
					cymoverheadlineunbalanced[row.DeviceNumber]['length'] = 1.0
				if _fixName(row.LineId) not in OhUbConductors:
					OhUbConductors.append(_fixName(row.LineId))
	return cymoverheadlineunbalanced, OhUbConductors

def _readCymeOverheadLine(feederId, modelDir):
	cymoverheadline = {}
	CYMOVERHEADLINE = { 'name' : None,
					'length': None,
					'configuration': None}
	lineIds = []
	overhead_line_db = _csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMOVERHEADLINE.csv"),feederId)
	if len(overhead_line_db) == 0:
		warnings.warn("No overhead_line objects were found in CYMOVERHEADLINE for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in overhead_line_db:
			row.DeviceNumber = _fixName(row.DeviceNumber)
			if _fixName(row.LineId) not in lineIds:
				lineIds.append(_fixName(row.LineId))
			if row.DeviceNumber not in cymoverheadline.keys():
				cymoverheadline[row.DeviceNumber] = copy.deepcopy(CYMOVERHEADLINE)
				cymoverheadline[row.DeviceNumber]['name'] = _fixName(row.DeviceNumber)  
				cymoverheadline[row.DeviceNumber]['configuration'] = _fixName(row.LineId)
				cymoverheadline[row.DeviceNumber]['length'] = float(row.Length)*m2ft
				if cymoverheadline[row.DeviceNumber]['length'] == 0.0:
					cymoverheadline[row.DeviceNumber]['length'] = 1.0
	return cymoverheadline, lineIds

def _readCymeQOverheadLine(feederId, modelDir):
	cymeqoverheadline = {}
	CYMEQOVERHEADLINE = { 'name' : None,       # Information structure for each object found in CYMOVERHEADBYPHASE
						  'configuration' : None}
	spacingIds = []
	cymeqoverheadline_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMEQOVERHEADLINE.csv"),feederId)
	if len(cymeqoverheadline_db) == 0:
		warnings.warn("No overheadline objects were found in CYMEQCONDUCTOR for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in cymeqoverheadline_db:
			row.EquipmentId = _fixName(row.EquipmentId)
			spacingIds.append(_fixName(row.ConductorSpacingId))
			if row.EquipmentId not in cymeqoverheadline.keys():
				cymeqoverheadline[row.EquipmentId] = copy.deepcopy(CYMEQOVERHEADLINE)
				cymeqoverheadline[row.EquipmentId]['name'] = row.EquipmentId               
				cymeqoverheadline[row.EquipmentId]['configuration'] = _fixName(row.PhaseConductorId)
				cymeqoverheadline[row.EquipmentId]['spacing'] = _fixName(row.ConductorSpacingId)
				cymeqoverheadline[row.EquipmentId]['conductor_N'] = _fixName(row.NeutralConductorId)
	return cymeqoverheadline, spacingIds

def _readCymeReactors(feederId, modelDir):
	cymseriesreactor = {}
	CYMSERIESREACTOR = { 'name' : None,
						 'configuration': None}
	reactorIds = []
	seriesreactor_db = _csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMSERIESREACTOR.csv"),feederId)
	if len(seriesreactor_db) == 0:
		warnings.warn("No series reactor objects were found in CYMSERIESREACTOR for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in seriesreactor_db:
			row.DeviceNumber = _fixName(row.DeviceNumber)
			if _fixName(row.EquipmentId) not in reactorIds:
				reactorIds.append(_fixName(row.EquipmentId))
			if row.DeviceNumber not in cymseriesreactor.keys():
				cymseriesreactor[row.DeviceNumber] = copy.deepcopy(CYMSERIESREACTOR)
				cymseriesreactor[row.DeviceNumber]['name'] = _fixName(row.DeviceNumber)
				cymseriesreactor[row.DeviceNumber]['configuration'] = _fixName(row.EquipmentId)

	return cymseriesreactor, reactorIds

def _readEqReactors(feederId, modelDir):
	cymeqreactor = {}
	CYMEQREACTOR = { 'name' : None,
					 'reactance': None}
	cymeqreactor_db = _csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMEQSERIESREACTOR.csv"),feederId)
	if len(cymeqreactor_db) == 0:
		warnings.warn("No reactor equipment was found in CYMEQREACTOR for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in cymeqreactor_db:
			row.EquipmentId = _fixName(row.EquipmentId)
			if row.EquipmentId not in cymeqreactor.keys():
				cymeqreactor[row.EquipmentId] = copy.deepcopy(CYMEQREACTOR)
				cymeqreactor[row.EquipmentId]['name'] = row.EquipmentId
				cymeqreactor[row.EquipmentId]['reactance'] = row.ReactanceOhms
	return cymeqreactor

def _readCymeSection(feederId, modelDir):
	'''store information from CYMSECTION'''
	cymsection = {}                         # Stores information found in CYMSECTION in the network database
	CYMSECTION = {  'name' : None,           # Information structure for each object found in CYMSECTION
								   'from' : None,
								   'to' : None,
								   'phases' : None}
	# section_db = networkDatabase.execute("SELECT SectionId, FromNodeId, ToNodeId, Phase FROM CYMSECTION WHERE NetworkId = '{:s}'".format(feederId)).fetchall()
	section_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMSECTION.csv"),feederId)
	if len(section_db) == 0:
		warnings.warn("No section information was found in CYMSECTION for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in section_db:
			row.SectionId = _fixName(row.SectionId)
			if row.SectionId not in cymsection.keys():
				cymsection[row.SectionId] = copy.deepcopy(CYMSECTION)
				cymsection[row.SectionId]['name'] = row.SectionId            
				cymsection[row.SectionId]['from'] = _fixName(row.FromNodeId)
				cymsection[row.SectionId]['to'] = _fixName(row.ToNodeId)
				cymsection[row.SectionId]['phases'] = _convertPhase(int(row.Phase))
	return cymsection

def _readCymeSectionDevice(feederId, modelDir):
	'''store information from CYMSECTIONDEVICE'''
	cymsectiondevice = {}                         # Stores information found in CYMSECTIONDEVICE in the network database
	CYMSECTIONDEVICE = { 'name' : None,           # Information structure for each object found in CYMSECTIONDEVICE
						'device_type' : None,
						'section_name' : None,
						'location' : None}
	# section_device_db = networkDatabase.execute("SELECT DeviceNumber, DeviceType, SectionId, Location FROM CYMSECTIONDEVICE WHERE NetworkId = '{:s}'".format(feederId)).fetchall()
	section_device_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMSECTIONDEVICE.csv"),feederId)
	if len(section_device_db) == 0:
		warnings.warn("No section device information was found in CYMSECTIONDEVICE for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in section_device_db:
			row.SectionId = _fixName(row.SectionId)
			row.DeviceNumber = _fixName(row.DeviceNumber)
			if row.DeviceNumber not in cymsectiondevice.keys(): 
				cymsectiondevice[row.DeviceNumber] = copy.deepcopy(CYMSECTIONDEVICE)
				cymsectiondevice[row.DeviceNumber]['name'] = row.DeviceNumber             
				cymsectiondevice[row.DeviceNumber]['device_type'] = int(row.DeviceType)
				cymsectiondevice[row.DeviceNumber]['section_name'] = row.SectionId
				cymsectiondevice[row.DeviceNumber]['location'] = int(row.Location)
			else:
				#jfk. A better fix is needed.
				print 'Found duplicate device ID: ' + row.DeviceNumber + '.  Rename device in Cyme or the device will be overwritten.'
	return cymsectiondevice

def _splitLinkObjects(sectionDict, deviceDict, linkDict, overheadDict, undergroundDict):
	'''Split multiple link objects from the line that they are folded into'''
	#jfk.  Several changes in here related to the following problem.  Old code assume that each section (linkDict) would
	#only have one device or link object per section.  I found that this wasn't true for solar PV and switches.
	#Later in the code, linkDicts for these objects have lists as their values.
	#This code now reflects this possiblity.  But it makes it kind of inconsistent and hacky.
	for link in linkDict.keys():
		if link in overheadDict.keys() or link in undergroundDict.keys(): # if true the link is embedded in a line object and must be separated
			lineId = link
			newLinkIds = linkDict[link] #jfk
			if type(newLinkIds) != list: #jfk
				newLinkIds = [newLinkIds]
			for newLinkId in newLinkIds:#jfk
				if deviceDict[newLinkId]['location'] == 1: # device is at the from side of a section
					sectionDict[newLinkId] = copy.deepcopy(sectionDict[lineId])
					sectionDict[newLinkId]['name'] = newLinkId
					sectionDict[newLinkId]['to'] = 'node' + newLinkId
					sectionDict[newLinkId]['toX'] = str(float(sectionDict[lineId]['fromX']) + random.uniform(-10,10))
					sectionDict[newLinkId]['toY'] = str(float(sectionDict[lineId]['fromY']) + random.uniform(-10,10))
					sectionDict[lineId]['from'] = 'node' + newLinkId
					sectionDict[lineId]['fromX'] = sectionDict[newLinkId]['toX']
					sectionDict[lineId]['fromY'] = sectionDict[newLinkId]['toY']
				else: # device is at the to side of a section
					sectionDict[newLinkId] = copy.deepcopy(sectionDict[lineId])
					sectionDict[newLinkId]['name'] = newLinkId
					sectionDict[newLinkId]['from'] = 'node' + newLinkId
					sectionDict[newLinkId]['fromX'] = str(float(sectionDict[lineId]['toX']) + random.uniform(-10,10))
					sectionDict[newLinkId]['fromY'] = str(float(sectionDict[lineId]['toY']) + random.uniform(-10,10))
					sectionDict[lineId]['to'] = 'node' + newLinkId
					sectionDict[lineId]['toX'] = sectionDict[newLinkId]['fromX']
					sectionDict[lineId]['toY'] = sectionDict[newLinkId]['fromY']
				for phase in ['N', 'D']:
					sectionDict[newLinkId]['phases'] = sectionDict[newLinkId]['phases'].replace(phase, '')
				deviceDict[newLinkId]['section_name'] = newLinkId
				deviceDict[newLinkId]['location'] = 0

def _findParents(sectionDict, deviceDict, loadDict):
	'''store parent information for load type objects'''
	for loadsection in loadDict.keys():
		lineId = loadsection
		# loaddevice = loadDict[lineId]
		if type(loadDict[lineId]) != list:
			loaddevices = [loadDict[lineId]]
		else:
			loaddevices = loadDict[lineId]
		for loaddevice in loaddevices:
			if deviceDict[loaddevice]['location'] == 2:
				deviceDict[loaddevice]['parent'] = sectionDict[lineId]['to']
			else:
				deviceDict[loaddevice]['parent'] = sectionDict[lineId]['from']
			deviceDict[loaddevice]['phases'] = sectionDict[lineId]['phases']

def _readCymeSwitch(feederId, modelDir):
	cymswitch = {}                          # Stores information found in CYMSWITCH in the network database
	CYMSWITCH = { 'name' : None,            # Information structure for each object found in CYMSWITCH
				  'equipment_name' : None,
				  'status' : None}
	# switch_db = networkDatabase.execute("SELECT DeviceNumber, EquipmentId, ClosedPhase FROM CYMSWITCH WHERE NetworkId = '{:s}'".format(feederId)).fetchall()
	switch_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMSWITCH.csv"),feederId)
	if len(switch_db) == 0:
		warnings.warn("No switch objects were found in CYMSWITCH for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in switch_db:
			row.DeviceNumber = _fixName(row.DeviceNumber)
			row.EquipmentId = _fixName(row.EquipmentId)
			if row.DeviceNumber not in cymswitch.keys():
				cymswitch[row.DeviceNumber] = copy.deepcopy(CYMSWITCH)
				cymswitch[row.DeviceNumber]['name'] = row.DeviceNumber             
				cymswitch[row.DeviceNumber]['equipment_name'] = row.EquipmentId
				if float(row.ClosedPhase) == 0.0:
					cymswitch[row.DeviceNumber]['status'] = 0
				else:
					cymswitch[row.DeviceNumber]['status'] = 1
	return cymswitch

def _readCymeSectionalizer(feederId, modelDir):
	cymsectionalizer = {}                           # Stores information found in CYMSECTIONALIZER in the network database
	CYMSECTIONALIZER = { 'name' : None,             # Information structure for each object found in CYMSECTIONALIZER
						 'status' : None}                 
	# sectionalizer_db = networkDatabase.execute("SELECT DeviceNumber, NormalStatus FROM CYMSECTIONALIZER WHERE NetworkId = '{:s}'".format(feederId)).fetchall()
	sectionalizer_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMSECTIONALIZER.csv"),feederId)
	if len(sectionalizer_db) == 0:
		warnings.warn("No sectionalizer objects were found in CYMSECTIONALIZER for feeder_id: {:s}.".format(feederId),RuntimeWarning)
	else:
		for row in sectionalizer_db:
			row.DeviceNumber = _fixName(row.DeviceNumber)
			if row.DeviceNumber not in cymsectionalizer.keys():
				cymsectionalizer[row.DeviceNumber] = copy.deepcopy(CYMSECTIONALIZER)
				cymsectionalizer[row.DeviceNumber]['name'] = row.DeviceNumber
				if float(row.NormalStatus) == 0:
					cymsectionalizer[row.DeviceNumber]['status'] = 0
				else:
					cymsectionalizer[row.DeviceNumber]['status'] = 1
	return cymsectionalizer

def _readCymeFuse(feederId, modelDir):
	cymfuse = {}                           # Stores information found in CYMFUSE in the network database
	CYMFUSE = { 'name' : None,             # Information structure for each object found in CYMFUSE
				'status' : None,
				'equipment_id' : None}
	# fuse_db = networkDatabase.execute("SELECT DeviceNumber, EquipmentId, NormalStatus FROM CYMFUSE WHERE NetworkId = '{:s}'".format(feederId)).fetchall()
	fuse_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMFUSE.csv"),feederId)
	if len(fuse_db) == 0:
		warnings.warn("No fuse objects were found in CYMFUSE for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in fuse_db:
			row.DeviceNumber = _fixName(row.DeviceNumber)
			row.EquipmentId = _fixName(row.EquipmentId)
			if row.DeviceNumber not in cymfuse.keys():
				cymfuse[row.DeviceNumber] = copy.deepcopy(CYMFUSE)
				cymfuse[row.DeviceNumber]['name'] = row.DeviceNumber
				cymfuse[row.DeviceNumber]['equipment_id'] = row.EquipmentId
				if float(row.NormalStatus) == 0:
					cymfuse[row.DeviceNumber]['status'] = 0
				else:
					cymfuse[row.DeviceNumber]['status'] = 1
	return cymfuse

def _readCymeRecloser(feederId, modelDir):
	cymrecloser = {}
	CYMRECLOSER = {    'name' : None,
					'status' : None}
	# recloser_db = networkDatabase.execute("SELECT DeviceNumber, NormalStatus FROM CYMRECLOSER WHERE NetworkId = '{:s}'".format(feederId)).fetchall()
	recloser_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMRECLOSER.csv"),feederId)
	if len(recloser_db) == 0:
		warnings.warn("No recloser objects were found in CYMRECLOSER for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in recloser_db:
			row.DeviceNumber = _fixName(row.DeviceNumber)
			if row.DeviceNumber not in cymrecloser.keys():
				cymrecloser[row.DeviceNumber] = copy.deepcopy(CYMRECLOSER)
				cymrecloser[row.DeviceNumber]['name'] = row.DeviceNumber
				if float(row.NormalStatus) == 0:
					cymrecloser[row.DeviceNumber]['status'] = 0
				else:
					cymrecloser[row.DeviceNumber]['status'] = 1
	return cymrecloser

def _readCymeRegulator(feederId, modelDir):
	cymregulator = {}                           # Stores information found in CYMREGULATOR in the network database
	CYMREGULATOR = { 'name' : None,             # Information structure for each object found in CYMREGULATOR
					 'equipment_name' : None,
					 'regulation' : None,
					 'band_width' : None,
					 'tap_pos_A' : None,
					 'tap_pos_B' : None,
					 'tap_pos_C' : None}
	# regulator_db = networkDatabase.execute("SELECT DeviceNumber, EquipmentId, BandWidth, BoostPercent, TapPositionA, TapPositionB, TapPositionC FROM CYMREGULATOR WHERE NetworkId = '{:s}'".format(feederId)).fetchall()
	regulator_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMREGULATOR.csv"),feederId)
	if len(regulator_db) == 0:
		warnings.warn("No regulator objects were found in CYMREGULATOR for feeder_id: {:s}".format(feederId), RuntimeWarning)
	else:
		for row in regulator_db:
			row.DeviceNumber = _fixName(row.DeviceNumber)
			row.EquipmentId = _fixName(row.EquipmentId)
			if row.DeviceNumber not in cymregulator.keys():
				cymregulator[row.DeviceNumber] = copy.deepcopy(CYMREGULATOR)
				cymregulator[row.DeviceNumber]['name'] = row.DeviceNumber          
				cymregulator[row.DeviceNumber]['equipment_name'] = row.EquipmentId
				# cymregulator[row.DeviceNumber]['band_width'] = float(row.BandWidth)/120.0 #does not exist in database.  now forwardbandwidth in regulator equipment
				cymregulator[row.DeviceNumber]['regulation'] = float(row.BoostPercent)/100.0
				cymregulator[row.DeviceNumber]['tap_pos_A'] = row.TapPositionA
				cymregulator[row.DeviceNumber]['tap_pos_B'] = row.TapPositionB
				cymregulator[row.DeviceNumber]['tap_pos_C'] = row.TapPositionC
	return cymregulator

def _readCymeShuntCapacitor(feederId, modelDir):
	cymshuntcapacitor = {}                           # Stores information found in CYMSHUNTCAPACITOR in the network database
	CYMSHUNTCAPACITOR = { 'name' : None,             # Information structure for each object found in CYMSHUNTCAPACITOR
						  'equipment_name' : None,
						  'status' : None,
						  'phases' : None,
						  'capacitor_A' : None,
						  'capacitor_B' : None,
						  'capacitor_C' : None,
						  'capacitor_ABC' : None,
						  'kV_line_neutral' : None, #kV. for consistency
						  'control' : None,
						  'voltage_set_high' : None,
						  'voltage_set_low' : None,
						  'VAr_set_high' : None,
						  'VAr_set_low' : None,
						  'current_set_high' : None,
						  'current_set_low' : None,
						  'pt_phase' : None,
						  'remote_sense': None,
						  'control_level': None}

	shuntcapacitor_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMSHUNTCAPACITOR.csv"),feederId)
	if len(shuntcapacitor_db) == 0:
		warnings.warn("No capacitor objects were found in CYMSHUNTCAPACITOR for feeder_id: {:s}".format(feederId), RuntimeWarning)
	else:
	# if shunt capacitor table has KVARBC as a column use this block:
		for row in shuntcapacitor_db:
			if row.SwitchedKVARA is None or float(row.SwitchedKVARA)==0.0:
				row.DeviceNumber = _fixName(row.DeviceNumber)
				if row.EquipmentId is None:
					row.EquipmentId = 'DEFAULT'
				row.EquipmentId = _fixName(row.EquipmentId)
				if row.DeviceNumber not in cymshuntcapacitor.keys():
					cymshuntcapacitor[row.DeviceNumber] = copy.deepcopy(CYMSHUNTCAPACITOR)
					cymshuntcapacitor[row.DeviceNumber]['name'] = row.DeviceNumber
					cymshuntcapacitor[row.DeviceNumber]['equipment_name'] = row.EquipmentId
					cymshuntcapacitor[row.DeviceNumber]['phases'] = 'ABC' # _convertPhase(int(row.Phase)) #jfk. Painful change.  Phase doesn't exist in my capacitor tables.
					cymshuntcapacitor[row.DeviceNumber]['status'] = row.Status
					if float(row.KVARA) == 0.0 and float(row.KVARA) == 0.0 and float(row.KVARA) == 0.0 and float(row.KVARABC) > 0.0:
						cymshuntcapacitor[row.DeviceNumber]['capacitor_A'] = float(row.KVARABC)*1000/3
						cymshuntcapacitor[row.DeviceNumber]['capacitor_B'] = float(row.KVARABC)*1000/3
						cymshuntcapacitor[row.DeviceNumber]['capacitor_C'] = float(row.KVARABC)*1000/3
					else:
						if float(row.KVARA) > 0.0:
							cymshuntcapacitor[row.DeviceNumber]['capacitor_A'] = float(row.KVARA)*1000
						if float(row.KVARB) > 0.0:
							cymshuntcapacitor[row.DeviceNumber]['capacitor_B'] = float(row.KVARB)*1000
						if float(row.KVARC) > 0.0:
							cymshuntcapacitor[row.DeviceNumber]['capacitor_C'] = float(row.KVARC)*1000
					if float(row.KVLN) > 0.0:
						cymshuntcapacitor[row.DeviceNumber]['kV_line_neutral'] = float(row.KVLN)*1000
					if int(row.CapacitorControlType) == 2:
						cymshuntcapacitor[row.DeviceNumber]['control'] = 'VAR'
						cymshuntcapacitor[row.DeviceNumber]['VAr_set_high'] = float(row.OnValue)*1000
						cymshuntcapacitor[row.DeviceNumber]['VAr_set_low'] = float(row.OffValue)*1000
						cymshuntcapacitor[row.DeviceNumber]['pt_phase'] = _convertPhase(int(row.Phase))
					elif int(row.CapacitorControlType) == 3:
						cymshuntcapacitor[row.DeviceNumber]['control'] = 'CURRENT'
						cymshuntcapacitor[row.DeviceNumber]['current_set_high'] = row.OnValue
						cymshuntcapacitor[row.DeviceNumber]['current_set_low'] = row.OffValue
						cymshuntcapacitor[row.DeviceNumber]['pt_phase'] = _convertPhase(int(row.Phase))
					elif int(row.CapacitorControlType) == 7:
						cymshuntcapacitor[row.DeviceNumber]['control'] = 'VOLT'
						controlledphase = _convertPhase(int(row.ControlledPhase)).replace('N','')
						cymshuntcapacitor[row.DeviceNumber]['voltage_set_low'] = float(row['OnValue'+controlledphase])
						cymshuntcapacitor[row.DeviceNumber]['voltage_set_high'] = float(row['OffValue'+controlledphase])
						cymshuntcapacitor[row.DeviceNumber]['pt_phase'] = controlledphase
						cymshuntcapacitor[row.DeviceNumber]['remote_sense'] = _fixName(row.ControlledNodeId)
					else:
						cymshuntcapacitor[row.DeviceNumber]['control'] = 'MANUAL'
						cymshuntcapacitor[row.DeviceNumber]['pt_phase'] = 'ABC' # _convertPhase(int(row.Phase)) #doesn't exist
						cymshuntcapacitor[row.DeviceNumber]['voltage_set_high'] = float(row.KVLN)*1000
						cymshuntcapacitor[row.DeviceNumber]['voltage_set_low'] = float(row.KVLN)*1000
			else:
				row.DeviceNumber = _fixName(row.DeviceNumber)
				if row.EquipmentId is None:
					row.EquipmentId = 'DEFAULT'
				row.EquipmentId = _fixName(row.EquipmentId)
				if row.DeviceNumber not in cymshuntcapacitor.keys():
					cymshuntcapacitor[row.DeviceNumber] = copy.deepcopy(CYMSHUNTCAPACITOR)
					cymshuntcapacitor[row.DeviceNumber]['name'] = row.DeviceNumber
					cymshuntcapacitor[row.DeviceNumber]['equipment_name'] = row.EquipmentId
					cymshuntcapacitor[row.DeviceNumber]['phases'] = "ABCN"
					cymshuntcapacitor[row.DeviceNumber]['status'] = row.Status
					if row.SwitchingMode == '2':
						cymshuntcapacitor[row.DeviceNumber]['control_level'] =  'BANK'
					elif row.SwitchingMode == '1':
						cymshuntcapacitor[row.DeviceNumber]['control_level'] =  'INDIVIDUAL'
					else:
						print 'could not find capacitor switching mode.  defaulting to INDIVIDUAL'
						cymshuntcapacitor[row.DeviceNumber]['control_level'] =  'INDIVIDUAL'
					if float(row.SwitchedKVARA) > 0.0:
						cymshuntcapacitor[row.DeviceNumber]['capacitor_A'] = float(row.SwitchedKVARA)*1000
					if float(row.SwitchedKVARB) > 0.0:
						cymshuntcapacitor[row.DeviceNumber]['capacitor_B'] = float(row.SwitchedKVARB)*1000
					if float(row.SwitchedKVARC) > 0.0:
						cymshuntcapacitor[row.DeviceNumber]['capacitor_C'] = float(row.SwitchedKVARC)*1000
					if float(row.KVLN) > 0.0:
						cymshuntcapacitor[row.DeviceNumber]['kV_line_neutral'] = float(row.KVLN)*1000
					if int(row.CapacitorControlType) == 2:
						cymshuntcapacitor[row.DeviceNumber]['control'] = 'VAR'
						cymshuntcapacitor[row.DeviceNumber]['VAr_set_high'] = float(row.OnValue)*1000
						cymshuntcapacitor[row.DeviceNumber]['VAr_set_low'] = float(row.OffValueA)*1000
						cymshuntcapacitor[row.DeviceNumber]['pt_phase'] = "ABCN"
					elif int(row.CapacitorControlType) == 3:
						cymshuntcapacitor[row.DeviceNumber]['control'] = 'CURRENT'
						cymshuntcapacitor[row.DeviceNumber]['current_set_high'] = row.OnValue
						cymshuntcapacitor[row.DeviceNumber]['current_set_low'] = row.OffValueA
						cymshuntcapacitor[row.DeviceNumber]['pt_phase'] = "ABCN"
					elif int(row.CapacitorControlType) == 7:
						cymshuntcapacitor[row.DeviceNumber]['control'] = 'VOLT'
                                                #print cymshuntcapacitor[row.DeviceNumber]['voltage_set_low']
						controlledphase = _convertPhase(int(row.ControlledPhase)).replace('N','')
                                                if row.get('OnValue' + controlledphase) is None:
                                                  row['OnValue' + controlledphase] = 0
                                                if row.get('OffValue' + controlledphase) is None:
                                                  row['OffValue' + controlledphase] = 0
						cymshuntcapacitor[row.DeviceNumber]['voltage_set_low'] = float(row['OnValue'+controlledphase])
						cymshuntcapacitor[row.DeviceNumber]['voltage_set_high'] = float(row['OffValue'+controlledphase])
						cymshuntcapacitor[row.DeviceNumber]['pt_phase'] = controlledphase#row.Phase doesn't exist
                                                if row.ControlledNodeId:
						  cymshuntcapacitor[row.DeviceNumber]['remote_sense'] = _fixName(row.ControlledNodeId)
                                                
                                                
					else:
						cymshuntcapacitor[row.DeviceNumber]['control'] = 'MANUAL'
						cymshuntcapacitor[row.DeviceNumber]['pt_phase'] = "ABCN"
						cymshuntcapacitor[row.DeviceNumber]['voltage_set_high'] = float(row.KVLN)*1000
						cymshuntcapacitor[row.DeviceNumber]['voltage_set_low'] = float(row.KVLN)*1000
	return cymshuntcapacitor

def _determineLoad( l_type, l_v1, l_v2, conKVA):
	l_real = 0
	l_imag = 0
	conKVA = float(conKVA)
	if l_type == 0: # information was stored as kW & kVAR
		l_real = l_v1 * 1000.0
		l_imag = abs(l_v2) * 1000.0
	elif l_type == 1: # information was stored as kVA & power factor
		l_real = l_v1 * abs(l_v2)/100.0 * 1000.0
		l_imag = l_v1 * math.sqrt(1 - (abs(l_v2)/100.0)**2) * 1000.0
	else: # information was stored as kW and power factor
		l_real = l_v1 * 1000.0
		if l_v2 != 0.0:
			l_imag = l_real/(abs(l_v2)/100.0)*math.sqrt(1-(abs(l_v2)/100.0)**2)
	if l_real == 0.0 and l_imag == 0.0:
			l_real = conKVA * abs(l_v2)/100.0 * 1000.0
			l_imag = conKVA * math.sqrt(1 - (abs(l_v2)/100.0)**2) * 1000.0
	if l_v2 < 0.0:
		l_imag *= -1.0
	return [l_real, l_imag]

def _setConstantPower(l_v2, l_real, l_imag):
	if l_v2 >= 0.0:
		cp_string = '{:0.3f}+{:0.3f}j'.format(l_real,l_imag)
	else:
		cp_string = '{:0.3f}-{:0.3f}j'.format(l_real,abs(l_imag))
	return cp_string

def _cleanPhases(phases):
	p = ''
	if 'A' in phases:
		p = p + 'A'
	if 'B' in phases:
		p = p + 'B'
	if 'C' in phases:
		p = p + 'C'
	return p

def _readCymeCustomerLoad(feederId, modelDir):
	cymcustomerload = {}                           # Stores information found in CYMCUSTOMERLOAD in the network database
	CYMCUSTOMERLOAD = { 'name' : None,             # Information structure for each object found in CYMCUSTERLOAD
					  'phases' : None,
					  'constant_power_A' : None,
					  'constant_power_B' : None,
					  'constant_power_C' : None,
					  'load_realA' : 0.0,
					  'load_imagA' : 0.0,
					  'load_realB' : 0.0,
					  'load_imagB' : 0.0,
					  'load_realC' : 0.0,
					  'load_imagC' : 0.0,
					  'load_class' : None}
	load_real = 0
	load_imag = 0
	# customerload_db = networkDatabase.execute("SELECT DeviceNumber, DeviceType, ConsumerClassId, Phase, LoadValueType, Phase, LoadValue1, LoadValue2, ConnectedKVA FROM CYMCUSTOMERLOAD WHERE NetworkId = '{:s}'".format(feederId)).fetchall()
	customerload_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMCUSTOMERLOAD.csv"),feederId)
	if len(customerload_db) == 0:
		warnings.warn("No load objects were found in CYMCUSTOMERLOAD for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in customerload_db:
			row.DeviceNumber = _fixName(row.DeviceNumber)
			if row.DeviceNumber not in cymcustomerload.keys():
				# check for 0 load
				[load_real, load_imag] = _determineLoad(int(row.LoadValueType), float(row.LoadValue1), float(row.LoadValue2), row.ConnectedKVA)
				if row.Status == '1': #jfk.  Set disconnected loads to zero.
					load_real = 0
					load_imag = 0

				cymcustomerload[row.DeviceNumber] = copy.deepcopy(CYMCUSTOMERLOAD)
				cymcustomerload[row.DeviceNumber]['name'] = row.DeviceNumber            
				cymcustomerload[row.DeviceNumber]['phases'] = _cleanPhases(_convertPhase(int(row.Phase)))
				# Determine the load classification
				if 'residential' in (row.ConsumerClassId).lower():
					cymcustomerload[row.DeviceNumber]['load_class'] = 'R'
				elif 'commercial' in (row.ConsumerClassId).lower():
					cymcustomerload[row.DeviceNumber]['load_class'] = 'C'
				else:
					cymcustomerload[row.DeviceNumber]['load_class'] = 'R'
				convert_class = _convertLoadClass(row.ConsumerClassId)
				if convert_class is not None:
					cymcustomerload[row.DeviceNumber]['load_class'] = convert_class
				
				if int(row.Phase) == 1:
					cymcustomerload[row.DeviceNumber]['load_realA'] = load_real
					cymcustomerload[row.DeviceNumber]['load_imagA'] = load_imag
					cymcustomerload[row.DeviceNumber]['constant_power_A'] = _setConstantPower(float(row.LoadValue2), load_real, load_imag)
				elif int(row.Phase) == 2:
					cymcustomerload[row.DeviceNumber]['load_realB'] = load_real
					cymcustomerload[row.DeviceNumber]['load_imagB'] = load_imag
					cymcustomerload[row.DeviceNumber]['constant_power_B'] = _setConstantPower(float(row.LoadValue2), load_real, load_imag)
				elif int(row.Phase) == 3:
					cymcustomerload[row.DeviceNumber]['load_realC'] = load_real
					cymcustomerload[row.DeviceNumber]['load_imagC'] = load_imag
					cymcustomerload[row.DeviceNumber]['constant_power_C'] = _setConstantPower(float(row.LoadValue2), load_real, load_imag)
				elif int(row.Phase) == 7:
					cymcustomerload[row.DeviceNumber]['load_realA'] = load_real/3.0
					cymcustomerload[row.DeviceNumber]['load_imagA'] = load_imag/3.0
					cymcustomerload[row.DeviceNumber]['constant_power_A'] = _setConstantPower(float(row.LoadValue2), load_real/3.0, load_imag/3.0)
					cymcustomerload[row.DeviceNumber]['load_realB'] = load_real/3.0
					cymcustomerload[row.DeviceNumber]['load_imagB'] = load_imag/3.0
					cymcustomerload[row.DeviceNumber]['constant_power_B'] = _setConstantPower(float(row.LoadValue2), load_real/3.0, load_imag/3.0)
					cymcustomerload[row.DeviceNumber]['load_realC'] = load_real/3.0
					cymcustomerload[row.DeviceNumber]['load_imagC'] = load_imag/3.0
					cymcustomerload[row.DeviceNumber]['constant_power_C'] = _setConstantPower(float(row.LoadValue2), load_real/3.0, load_imag/3.0)
			else:
				[load_real, load_imag] = _determineLoad(int(row.LoadValueType), float(row.LoadValue1), float(row.LoadValue2), float(row.ConnectedKVA))
				ph = cymcustomerload[row.DeviceNumber]['phases'] + _convertPhase(int(row.Phase))
				cymcustomerload[row.DeviceNumber]['phases'] = _cleanPhases(ph)
				if int(row.Phase) == 1:
					cymcustomerload[row.DeviceNumber]['load_realA'] += load_real
					cymcustomerload[row.DeviceNumber]['load_imagA'] += load_imag
					cymcustomerload[row.DeviceNumber]['constant_power_A'] = _setConstantPower(float(row.LoadValue2), cymcustomerload[row.DeviceNumber]['load_realA'], cymcustomerload[row.DeviceNumber]['load_imagA'])
				elif int(row.Phase) == 2:
					cymcustomerload[row.DeviceNumber]['load_realB'] += load_real
					cymcustomerload[row.DeviceNumber]['load_imagB'] += load_imag
					cymcustomerload[row.DeviceNumber]['constant_power_B'] = _setConstantPower(float(row.LoadValue2), cymcustomerload[row.DeviceNumber]['load_realB'], cymcustomerload[row.DeviceNumber]['load_imagB'])
				elif int(row.Phase) == 3:
					cymcustomerload[row.DeviceNumber]['load_realC'] += load_real
					cymcustomerload[row.DeviceNumber]['load_imagC'] += load_imag
					cymcustomerload[row.DeviceNumber]['constant_power_C'] = _setConstantPower(float(row.LoadValue2), cymcustomerload[row.DeviceNumber]['load_realC'], cymcustomerload[row.DeviceNumber]['load_imagC'])
				elif int(row.Phase) == 7:
					cymcustomerload[row.DeviceNumber]['load_realA'] += load_real/3.0
					cymcustomerload[row.DeviceNumber]['load_imagA'] += load_imag/3.0
					cymcustomerload[row.DeviceNumber]['constant_power_A'] = _setConstantPower(float(row.LoadValue2), cymcustomerload[row.DeviceNumber]['load_realA'], cymcustomerload[row.DeviceNumber]['load_imagA'])
					cymcustomerload[row.DeviceNumber]['load_realB'] += load_real/3.0
					cymcustomerload[row.DeviceNumber]['load_imagB'] += load_imag/3.0
					cymcustomerload[row.DeviceNumber]['constant_power_B'] = _setConstantPower(float(row.LoadValue2), cymcustomerload[row.DeviceNumber]['load_realB'], cymcustomerload[row.DeviceNumber]['load_imagB'])
					cymcustomerload[row.DeviceNumber]['load_realC'] += load_real/3.0
					cymcustomerload[row.DeviceNumber]['load_imagC'] += load_imag/3.0
					cymcustomerload[row.DeviceNumber]['constant_power_C'] = _setConstantPower(float(row.LoadValue2), cymcustomerload[row.DeviceNumber]['load_realC'], cymcustomerload[row.DeviceNumber]['load_imagC'])
	return cymcustomerload

def _readCymeThreeWindingTransformer(feederId, modelDir):
	cymthreewxfmr = {}                           # Stores information found in CYMREGULATOR in the network database
	CYMTHREEWXFMR = { 'name' : None,             # Information structure for each object found in CYMREGULATOR
					 'equipment_name' : None}                 
	# threewxfmr_db = networkDatabase.execute("SELECT DeviceNumber, EquipmentId FROM CYMTHREEWINDINGTRANSFORMER WHERE NetworkId = '{:s}'".format(feederId)).fetchall()
	threewxfmr_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMTHREEWINDINGTRANSFORMER.csv"),feederId)
	if len(threewxfmr_db) == 0:
		warnings.warn("No three-winding transformer objects were found in CYMTHREEWINDINGTRANSFORMER for feeder_id: {:s}".format(feederId), RuntimeWarning)
	else:
		for row in threewxfmr_db:
			row.DeviceNumber = _fixName(row.DeviceNumber)
			row.EquipmentId = _fixName(row.EquipmentId)
			if row.DeviceNumber not in cymthreewxfmr.keys():
				cymthreewxfmr[row.DeviceNumber] = copy.deepcopy(CYMTHREEWXFMR)
				cymthreewxfmr[row.DeviceNumber]['name'] = row.DeviceNumber           
				cymthreewxfmr[row.DeviceNumber]['equipment_name'] = row.EquipmentId
	return cymthreewxfmr

def _readCymeTransformer(feederId, modelDir):
	cymxfmr = {}
	CYMXFMR = { 'name' : None,
			   'equipment_name' : None}
	# xfmrDb = networkDatabase.execute("SELECT DeviceNumber, EquipmentId FROM CYMTRANSFORMER WHERE NetworkId = '{:s}'".format(feederId)).fetchall()
	xfmrDb =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMTRANSFORMER.csv"),feederId)
	if len(xfmrDb) == 0:
		warnings.warn("No transformer objects were found in CYMTRANSFORMER for feeder id: {:s}".format(feederId), RuntimeWarning)
	else:
		for row in xfmrDb:
			row.DeviceNumber = _fixName(row.DeviceNumber)
			row.EquipmentId = _fixName(row.EquipmentId)
			if row.DeviceNumber not in cymxfmr.keys():
				cymxfmr[row.DeviceNumber] = copy.deepcopy(CYMXFMR)
				cymxfmr[row.DeviceNumber]['name'] = row.DeviceNumber
				cymxfmr[row.DeviceNumber]['equipment_name'] = row.EquipmentId
	return cymxfmr

def _readEqConductor(feederId, modelDir):
	cymeqconductor = {}                           # Stores information found in CYMEQCONDUCTOR in the equipment database
	CYMEQCONDUCTOR = { 'name' : None,             # Information structure for each object found in CYMEQCONDUCTOR
					   'rating.summer_continuous' : None,
					   'geometric_mean_radius' : None,
					   'resistance' : None}
	cymeqconductor_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMEQCONDUCTOR.csv"),feederId)
	if len(cymeqconductor_db) == 0:
		warnings.warn("No conductor objects were found in CYMEQCONDUCTOR for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in cymeqconductor_db:
			row.EquipmentId = _fixName(row.EquipmentId)
			if row.EquipmentId not in cymeqconductor.keys():
				cymeqconductor[row.EquipmentId] = copy.deepcopy(CYMEQCONDUCTOR)
				cymeqconductor[row.EquipmentId]['name'] = row.EquipmentId               
				cymeqconductor[row.EquipmentId]['rating.summer_continuous'] = row.FirstRating
				cymeqconductor[row.EquipmentId]['geometric_mean_radius'] = float(row.GMR)*m2ft/100 #GMR is stored in cm. Must convert to ft.
				cymeqconductor[row.EquipmentId]['resistance'] = float(row.R50)*5280/(m2ft*1000) # R50 is stored in Ohm/km. Must convert to Ohm/mile
	return cymeqconductor

def _readEqOverheadLineUnbalanced(feederId, modelDir):
	'''store information from CYMEQOVERHEADLINEUNBALANCED'''
	cymeqoverheadlineunbalanced = {}                         # Stores information found in CYMEQOVERHEADLINEUNBALANCED in the network database
	CYMEQOVERHEADLINEUNBALANCED = { 'object' : 'line_configuration',
																			'name' : None,
																			'z11' : None,
																			'z12' : None,
																			'z13' : None,
																			'z21' : None,
																			'z22' : None,
																			'z23' : None,
																			'z31' : None,
																			'z32' : None,
																			'z33' : None}
	# ug_line_db = networkDatabase.execute("SELECT EquipmentId, SelfResistanceA, SelfResistanceB, SelfResistanceC, SelfReactanceA, SelfReactanceB, SelfReactanceC, MutualResistanceAB, MutualResistanceBC, MutualResistanceCA, MutualReactanceAB, MutualReactanceBC, MutualReactanceCA FROM CYMEQOVERHEADLINEUNBALANCED WHERE EquipmentId = '{:s}'".format("LINE606")).fetchall()
	oh_line_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMEQOVERHEADLINEUNBALANCED.csv"),feederId)
	if len(oh_line_db) == 0:
		warnings.warn("No underground_line configuration objects were found in CYMEQOVERHEADLINEUNBALANCED for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in oh_line_db:
			row.EquipmentId = _fixName(row.EquipmentId)
			if row.EquipmentId not in cymeqoverheadlineunbalanced.keys():
				cymeqoverheadlineunbalanced[row.EquipmentId] = copy.deepcopy(CYMEQOVERHEADLINEUNBALANCED)
				cymeqoverheadlineunbalanced[row.EquipmentId]['name'] = _fixName(row.EquipmentId)  
				cymeqoverheadlineunbalanced[row.EquipmentId]['z11'] ='{:0.6f}{:+0.6}j'.format(float(row.SelfResistanceA)*5280/(m2ft*1000), float(row.SelfReactanceA)*5280/(m2ft*1000)) #  Ohm/km. Must convert to Ohm/mile
				cymeqoverheadlineunbalanced[row.EquipmentId]['z22'] ='{:0.6f}{:+0.6}j'.format(float(row.SelfResistanceB)*5280/(m2ft*1000), float(row.SelfReactanceB)*5280/(m2ft*1000)) 
				cymeqoverheadlineunbalanced[row.EquipmentId]['z33'] ='{:0.6f}{:+0.6}j'.format(float(row.SelfResistanceC)*5280/(m2ft*1000), float(row.SelfReactanceC)*5280/(m2ft*1000))
				cymeqoverheadlineunbalanced[row.EquipmentId]['z12'] ='{:0.6f}{:+0.6}j'.format(float(row.MutualResistanceAB)*5280/(m2ft*1000), float(row.MutualReactanceAB)*5280/(m2ft*1000))
				cymeqoverheadlineunbalanced[row.EquipmentId]['z21'] ='{:0.6f}{:+0.6}j'.format(float(row.MutualResistanceAB)*5280/(m2ft*1000), float(row.MutualReactanceAB)*5280/(m2ft*1000))  
				cymeqoverheadlineunbalanced[row.EquipmentId]['z23'] ='{:0.6f}{:+0.6}j'.format(float(row.MutualResistanceBC)*5280/(m2ft*1000), float(row.MutualReactanceBC)*5280/(m2ft*1000))  
				cymeqoverheadlineunbalanced[row.EquipmentId]['z32'] ='{:0.6f}{:+0.6}j'.format(float(row.MutualResistanceBC)*5280/(m2ft*1000), float(row.MutualReactanceBC)*5280/(m2ft*1000))  
				cymeqoverheadlineunbalanced[row.EquipmentId]['z13'] ='{:0.6f}{:+0.6}j'.format(float(row.MutualResistanceCA)*5280/(m2ft*1000), float(row.MutualReactanceCA)*5280/(m2ft*1000))  
				cymeqoverheadlineunbalanced[row.EquipmentId]['z31'] ='{:0.6f}{:+0.6}j'.format(float(row.MutualResistanceCA)*5280/(m2ft*1000), float(row.MutualReactanceCA)*5280/(m2ft*1000))  
	return cymeqoverheadlineunbalanced

def _readEqGeometricalArrangement(feederId, modelDir):
	cymeqgeometricalarrangement = {}                           # Stores information found in CYMEQGEOMETRICALARRANGEMENT in the equipment database
	CYMEQGEOMETRICALARRANGEMENT = { 'name' : None,             # Information structure for each object found in CYMEQGEOMETRICALARRANGEMENT
									'distance_AB' : None,
									'distance_AC' : None,
									'distance_AN' : None,
									'distance_BC' : None,
									'distance_BN' : None,
									'distance_CN' : None}
	# cymeqgeometricalarrangement_db = equipmentDatabase.execute("SELECT EquipmentId, ConductorA_Horizontal, ConductorA_Vertical, ConductorB_Horizontal, ConductorB_Vertical, ConductorC_Horizontal, ConductorC_Vertical, NeutralConductor_Horizontal, NeutralConductor_Vertical FROM CYMEQGEOMETRICALARRANGEMENT").fetchall()
	cymeqgeometricalarrangement_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMEQGEOMETRICALARRANGEMENT.csv"),feederId)
	if len(cymeqgeometricalarrangement_db) == 0:
		warnings.warn("No geometric spacing information was found in CYMEQGEOMETRICALARRANGEMENT for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in cymeqgeometricalarrangement_db:
			row.EquipmentId = _fixName(row.EquipmentId)
			if row.EquipmentId not in cymeqgeometricalarrangement.keys():
				cymeqgeometricalarrangement[row.EquipmentId] = copy.deepcopy(CYMEQGEOMETRICALARRANGEMENT)
				cymeqgeometricalarrangement[row.EquipmentId]['name'] = row.EquipmentId              
				cymeqgeometricalarrangement[row.EquipmentId]['distance_AB'] = math.sqrt((float(row.ConductorA_Horizontal)-float(row.ConductorB_Horizontal))**2 + (float(row.ConductorA_Vertical)-float(row.ConductorB_Vertical))**2)*m2ft # information is stored in meters. must convert to feet.
				cymeqgeometricalarrangement[row.EquipmentId]['distance_AC'] = math.sqrt((float(row.ConductorA_Horizontal)-float(row.ConductorC_Horizontal))**2 + (float(row.ConductorA_Vertical)-float(row.ConductorC_Vertical))**2)*m2ft # information is stored in meters. must convert to feet.
				cymeqgeometricalarrangement[row.EquipmentId]['distance_AN'] = math.sqrt((float(row.ConductorA_Horizontal)-float(row.NeutralConductor_Horizontal))**2 + (float(row.ConductorA_Vertical)-float(row.NeutralConductor_Vertical))**2)*m2ft # information is stored in meters. must convert to feet.
				cymeqgeometricalarrangement[row.EquipmentId]['distance_BC'] = math.sqrt((float(row.ConductorC_Horizontal)-float(row.ConductorB_Horizontal))**2 + (float(row.ConductorC_Vertical)-float(row.ConductorB_Vertical))**2)*m2ft # information is stored in meters. must convert to feet.
				cymeqgeometricalarrangement[row.EquipmentId]['distance_BN'] = math.sqrt((float(row.NeutralConductor_Horizontal)-float(row.ConductorB_Horizontal))**2 + (float(row.NeutralConductor_Vertical)-float(row.ConductorB_Vertical))**2)*m2ft # information is stored in meters. must convert to feet.
				cymeqgeometricalarrangement[row.EquipmentId]['distance_CN'] = math.sqrt((float(row.ConductorC_Horizontal)-float(row.NeutralConductor_Horizontal))**2 + (float(row.ConductorC_Vertical)-float(row.NeutralConductor_Vertical))**2)*m2ft # information is stored in meters. must convert to feet.
	return cymeqgeometricalarrangement

def _readUgConfiguration(feederId, modelDir):
	cymcsvundergroundcable = {}
	# Defaults, need defaults for all values
	CYMCSVUNDERGROUNDCABLE = { 'name' : None,
							   'rating.summer_continuous' : None,
							   'outer_diameter' : 0.0640837,
							   'conductor_resistance' : 14.87200,
							   'conductor_gmr' : 0.020800,
							   'conductor_diameter' : 0.0640837,
							   'neutral_resistance' : 14.87200,
							   'neutral_gmr' : 0.020800,
							   'neutral_diameter' : 0.0640837,
							   'neutral_strands' : 10,
							   'distance_AB' : 0.05,
							   'distance_AC' : 1.0,
							   'distance_AN' : 0.0,
							   'distance_BC' : 0.5,
							   'distance_BN' : 0.0,
							   'distance_CN' : 0.0,
							   'z11': 0 + 1j,
							   'z12': 0 + 1j,
							   'z13': 0 + 1j,
							   'z21': 0 + 1j,
							   'z22': 0 + 1j,
							   'z23': 0 + 1j,
							   'z31': 0 + 1j,
							   'z32': 0 + 1j,
							   'z33': 0 + 1j}
	try:
		undergroundcable = _csvToDictList(pJoin(modelDir,'cymeCsvDump','CYMEQCABLE.csv'),feederId)
		undergroundcableconductor = _csvToDictList(pJoin(modelDir,'cymeCsvDump','CYMEQCABLECONDUCTOR.csv'),feederId)
	except:
		undergroundcableconductor = {}
		warnings.warn("No underground_line configuration objects were found in CYMEQCABLE for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	if len(undergroundcable) == 0:
		warnings.warn("No underground_line configuration objects were found in CYMEQCABLE for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	else:
		#declare some conversion matrices for impedance conversion later
		a_s = 1*np.exp(1j*np.deg2rad(120))
		As = np.array([[1, 1, 1],[1, a_s**2, a_s],[1, a_s, a_s**2]])
		for row in undergroundcable:
			row.EquipmentId = _fixName(row.EquipmentId)
			if row.EquipmentId not in cymcsvundergroundcable.keys():
				cymcsvundergroundcable[row.EquipmentId] = copy.deepcopy(CYMCSVUNDERGROUNDCABLE)
				cymcsvundergroundcable[row.EquipmentId]['name'] = _fixName(row.EquipmentId)
				cymcsvundergroundcable[row.EquipmentId]['rating.summer_continuous'] = row.FirstRating
				if row.OverallDiameter is not None:
					cymcsvundergroundcable[row.EquipmentId]['outer_diameter'] = row.OverallDiameter
				cymcsvundergroundcable[row.EquipmentId]['conductor_resistance'] = row.PositiveSequenceResistance#leaving as is since z matrix overwrites
				if row.ArmorOuterDiameter is not None and row.ArmorOuterDiameter != '' and float(row.ArmorOuterDiameter) != 0.0:#jfk
					cymcsvundergroundcable[row.EquipmentId]['conductor_diameter'] = row.ArmorOuterDiameter
					cymcsvundergroundcable[row.EquipmentId]['conductor_gmr'] = float(row.ArmorOuterDiameter)/3

				#conversion from cyme's ZeroSequenceResistance/Reactance -> Gridlabd's self/mutual impedances
				z00 =  complex(float(row.ZeroSequenceResistance),float(row.ZeroSequenceReactance))
				z11 =  complex(float(row.PositiveSequenceResistance),float(row.PositiveSequenceReactance))
				Z012 = np.array([[z00, 0, 0], [0, z11, 0],[0, 0, z11]])*5280/(m2ft*1000)
				Zabc = As.dot(Z012).dot(inv(As))
				cymcsvundergroundcable[row.EquipmentId]['z11'] = '{:0.6f}'.format(Zabc[0][0].real) + '{:+0.6f}'.format(Zabc[0][0].imag)+'j'
				cymcsvundergroundcable[row.EquipmentId]['z12'] = '{:0.6f}'.format(Zabc[0][1].real) + '{:+0.6f}'.format(Zabc[0][1].imag)+'j'
				cymcsvundergroundcable[row.EquipmentId]['z13'] = '{:0.6f}'.format(Zabc[0][2].real) + '{:+0.6f}'.format(Zabc[0][2].imag)+'j'
				cymcsvundergroundcable[row.EquipmentId]['z21'] = '{:0.6f}'.format(Zabc[1][0].real) + '{:+0.6f}'.format(Zabc[1][0].imag)+'j'
				cymcsvundergroundcable[row.EquipmentId]['z22'] = '{:0.6f}'.format(Zabc[1][1].real) + '{:+0.6f}'.format(Zabc[1][1].imag)+'j'
				cymcsvundergroundcable[row.EquipmentId]['z23'] = '{:0.6f}'.format(Zabc[1][2].real) + '{:+0.6f}'.format(Zabc[1][2].imag)+'j'
				cymcsvundergroundcable[row.EquipmentId]['z31'] = '{:0.6f}'.format(Zabc[2][0].real) + '{:+0.6f}'.format(Zabc[2][0].imag)+'j'
				cymcsvundergroundcable[row.EquipmentId]['z32'] = '{:0.6f}'.format(Zabc[2][1].real) + '{:+0.6f}'.format(Zabc[2][1].imag)+'j'
				cymcsvundergroundcable[row.EquipmentId]['z33'] = '{:0.6f}'.format(Zabc[2][2].real) + '{:+0.6f}'.format(Zabc[2][2].imag)+'j'

				# Still missing these properties, will have default values for all objects
				# cymcsvundergroundcable[row.EquipmentId]['neutral_resistance'] = row.ZeroSequenceResistance
				# cymcsvundergroundcable[row.EquipmentId]['distance_AB'] = row.OverallDiameter
				# cymcsvundergroundcable[row.EquipmentId]['distance_AC'] = row.OverallDiameter
				# cymcsvundergroundcable[row.EquipmentId]['distance_AN'] = row.OverallDiameter
				# cymcsvundergroundcable[row.EquipmentId]['distance_BC'] = row.OverallDiameter
				# cymcsvundergroundcable[row.EquipmentId]['distance_BC'] = row.OverallDiameter
				# cymcsvundergroundcable[row.EquipmentId]['distance_CN'] = row.OverallDiameter
	for row in undergroundcableconductor:
		row.EquipmentId = _fixName(row.EquipmentId) #jfk.  was missing _fixName
		if row.EquipmentId in cymcsvundergroundcable.keys():
			cymcsvundergroundcable[row.EquipmentId]['neutral_diameter'] = row.Diameter
			cymcsvundergroundcable[row.EquipmentId]['neutral_strands'] = row.NumberOfStrands
			cymcsvundergroundcable[row.EquipmentId]['neutral_gmr'] = float(row.Diameter)/3
	return cymcsvundergroundcable

def _readEqAvgGeometricalArrangement(feederId, modelDir):
	cymeqgeometricalarrangement = {}
	CYMEQGEOMETRICALARRANGEMENT = {'name' : None,
								 'distance_AB' : None,
								 'distance_AC' : None,
								 'distance_AN' : None,
								 'distance_BC' : None,
								 'distance_BN' : None,
								 'distance_CN' : None}
	# cymeqaveragegeoarrangement_db = equipmentDatabase.execute("SELECT EquipmentId, GMDPhaseToPhase, GMDPhaseToNeutral FROM CYMEQAVERAGEGEOARRANGEMENT").fetchall()
	cymeqaveragegeoarrangement_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMEQAVERAGEGEOARRANGEMENT.csv"),feederId)
	if len(cymeqaveragegeoarrangement_db) == 0:
		warnings.warn("No average spacing information was found in CYMEQAVERAGEGEOARRANGEMENT for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in cymeqaveragegeoarrangement_db:
			row.EquipmentId = _fixName(row.EquipmentId)
			if row.EquipmentId not in cymeqgeometricalarrangement.keys():
				cymeqgeometricalarrangement[row.EquipmentId] = copy.deepcopy(CYMEQGEOMETRICALARRANGEMENT)
				cymeqgeometricalarrangement[row.EquipmentId]['name'] = row.EquipmentId             
				cymeqgeometricalarrangement[row.EquipmentId]['distance_AB'] = float(row.GMDPhaseToPhase)*m2ft # information is stored in meters. must convert to feet.
				cymeqgeometricalarrangement[row.EquipmentId]['distance_AC'] = float(row.GMDPhaseToPhase)*m2ft
				cymeqgeometricalarrangement[row.EquipmentId]['distance_AN'] = float(row.GMDPhaseToNeutral)*m2ft
				cymeqgeometricalarrangement[row.EquipmentId]['distance_BC'] = float(row.GMDPhaseToPhase)*m2ft
				cymeqgeometricalarrangement[row.EquipmentId]['distance_BN'] = float(row.GMDPhaseToNeutral)*m2ft
				cymeqgeometricalarrangement[row.EquipmentId]['distance_CN'] = float(row.GMDPhaseToNeutral)*m2ft
	return cymeqgeometricalarrangement

def _readEqRegulator(feederId, modelDir):
	cymeqregulator = {}                           # Stores information found in CYMEQREGULATOR in the equipment database
	CYMEQREGULATOR = { 'name' : None,             # Information structure for each object found in CYMEQREGULATOR
					   'raise_taps' : None,
					   'lower_taps' : None,
					   'nominal_voltage': None,
					   'bandwidth': None}
	# cymeqregulator_db = equipmentDatabase.execute("SELECT EquipmentId, NumberOfTaps FROM CYMEQREGULATOR").fetchall()
	cymeqregulator_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMEQREGULATOR.csv"),feederId)

	if len(cymeqregulator_db) == 0:
		warnings.warn("No regulator equipment was found in CYMEQREGULATOR for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in cymeqregulator_db:
			row.EquipmentId = _fixName(row.EquipmentId)
			if row.EquipmentId not in cymeqregulator.keys():
				cymeqregulator[row.EquipmentId] = copy.deepcopy(CYMEQREGULATOR)
				cymeqregulator[row.EquipmentId]['name'] = row.EquipmentId           
				cymeqregulator[row.EquipmentId]['raise_taps'] = str(int(float(row.NumberOfTaps) * 0.5))
				cymeqregulator[row.EquipmentId]['lower_taps'] = str(int(float(row.NumberOfTaps) * 0.5))
				cymeqregulator[row.EquipmentId]['nominal_voltage'] = row.RatedKVLN
				cymeqregulator[row.EquipmentId]['bandwidth'] = row.ForwardBandwidth
	return cymeqregulator

def _readEqThreeWAutoXfmr(feederId, modelDir):
	cymeqthreewautoxfmr = {}                           # Stores information found in CYMEQOVERHEADLINE in the equipment database
	CYMEQTHREEWAUTOXFMR = { 'name' : None,             # Information structure for each object found in CYMEQOVERHEADLINE
						  'PrimaryRatedCapacity' : None,
						  'PrimaryVoltage' : None,
						  'SecondaryVoltage' : None,
						  'impedance' : None}

	# cymeqthreewautoxfmr_db = equipmentDatabase.execute("SELECT EquipmentId, PrimaryRatedCapacity, PrimaryVoltage, SecondaryVoltage, PrimarySecondaryZ1, PrimarySecondaryZ0, PrimarySecondaryXR1Ratio, PrimarySecondaryXR0Ratio  FROM CYMEQTHREEWINDAUTOTRANSFORMER").fetchall()
	cymeqthreewautoxfmr_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMEQTHREEWINDAUTOTRANSFORMER.csv"),feederId)
	if len(cymeqthreewautoxfmr_db) == 0:
		warnings.warn("No average spacing information was found in CYMEQTHREEWINDAUTOTRANSFORMER for feeder_id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in cymeqthreewautoxfmr_db:
			row.EquipmentId = _fixName(row.EquipmentId)
			if row.EquipmentId not in cymeqthreewautoxfmr.keys():
				cymeqthreewautoxfmr[row.EquipmentId] = copy.deepcopy(CYMEQTHREEWAUTOXFMR)
				cymeqthreewautoxfmr[row.EquipmentId]['name'] = row.EquipmentId           
				cymeqthreewautoxfmr[row.EquipmentId]['PrimaryRatedCapacity'] = float(row.PrimaryRatedCapacity)
				cymeqthreewautoxfmr[row.EquipmentId]['PrimaryVoltage'] = float(row.PrimaryVoltage)*1000.0/math.sqrt(3.0)
				cymeqthreewautoxfmr[row.EquipmentId]['SecondaryVoltage'] = float(row.SecondaryVoltage)*1000.0/math.sqrt(3.0)
				if cymeqthreewautoxfmr[row.EquipmentId]['PrimaryVoltage'] == cymeqthreewautoxfmr[row.EquipmentId]['SecondaryVoltage']:
					cymeqthreewautoxfmr[row.EquipmentId]['SecondaryVoltage'] += 0.1
				z1mag = float(row.PrimarySecondaryZ1)/100.0
				r = z1mag/math.sqrt(1+(float(row.PrimarySecondaryXR1Ratio))**2)
				if r == 0.0:
					r = 0.000333
					x = 0.00222
				else:
					x = r*float(row.PrimarySecondaryXR1Ratio)
				cymeqthreewautoxfmr[row.EquipmentId]['impedance'] = '{:0.6f}{:+0.6f}j'.format(r, x)
	return cymeqthreewautoxfmr

def _readEqAutoXfmr(feederId, modelDir):
	cymeqautoxfmr = {}
	CYMEQAUTOXFMR = { 'name' : None,
					 'PrimaryRatedCapacity' : None,
					 'PrimaryVoltage' : None,
					 'SecondaryVoltage' : None,
					 'impedance' : None}
	# cymeqautoxfmr_db = equipmentDatabase.execute("SELECT EquipmentId, NominalRatingKVA, PrimaryVoltageKVLL, SecondaryVoltageKVLL, PosSeqImpedancePercent, XRRatio FROM CYMEQAUTOTRANSFORMER").fetchall()
	cymeqautoxfmr_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMEQAUTOTRANSFORMER.csv"),feederId)
	if len(cymeqautoxfmr_db) == 0:
		warnings.warn("No average autotransformer equipment information was found in CYMEQAUTOTRANSFORMER for feeder id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in cymeqautoxfmr_db:
			row.EquipmentId = _fixName(row.EquipmentId)
			if row.EquipmentId not in cymeqautoxfmr.keys():
				cymeqautoxfmr[row.EquipmentId] = copy.deepcopy(CYMEQAUTOXFMR)
				cymeqautoxfmr[row.EquipmentId]['name'] = row.EquipmentId           
				cymeqautoxfmr[row.EquipmentId]['PrimaryRatedCapacity'] = float(row.NominalRatingKVA)
				cymeqautoxfmr[row.EquipmentId]['PrimaryVoltage'] = float(row.PrimaryVoltageKVLL)*1000.0/math.sqrt(3.0)
				cymeqautoxfmr[row.EquipmentId]['SecondaryVoltage'] = float(row.SecondaryVoltageKVLL)*1000.0/math.sqrt(3.0)
				if cymeqautoxfmr[row.EquipmentId]['PrimaryVoltage'] == cymeqautoxfmr[row.EquipmentId]['SecondaryVoltage']:
					cymeqautoxfmr[row.EquipmentId]['SecondaryVoltage'] += 0.001
				z1mag = float(row.PosSeqImpedancePercent)/100.0
				r = z1mag/math.sqrt(1+(float(row.XRRatio))**2)
				if r == 0.0:
					r = 0.000333
					x = 0.00222
				else:
					x = r*float(row.XRRatio)
				cymeqautoxfmr[row.EquipmentId]['impedance'] = '{:0.6f}{:+0.6f}j'.format(r, x)
	return cymeqautoxfmr

def _readEqXfmr(feederId, modelDir):
	cymeqxfmr = {}
	CYMEQXFMR = { 'name' : None,
					 'PrimaryRatedCapacity' : None,
					 'PrimaryVoltage' : None,
					 'SecondaryVoltage' : None,
					 'impedance' : None}
	# cymeqautoxfmr_db = equipmentDatabase.execute("SELECT EquipmentId, NominalRatingKVA, PrimaryVoltageKVLL, SecondaryVoltageKVLL, PosSeqImpedancePercent, XRRatio FROM CYMEQAUTOTRANSFORMER").fetchall()
	cymeqxfmr_db =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMEQTRANSFORMER.csv"),feederId)
	if len(cymeqxfmr_db) == 0:
		warnings.warn("No average transformer equipment information was found in CYMEQTRANSFORMER for feeder id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in cymeqxfmr_db:
			row.EquipmentId = _fixName(row.EquipmentId)
			if row.EquipmentId not in cymeqxfmr.keys():
				cymeqxfmr[row.EquipmentId] = copy.deepcopy(CYMEQXFMR)
				cymeqxfmr[row.EquipmentId]['name'] = row.EquipmentId
				cymeqxfmr[row.EquipmentId]['PrimaryRatedCapacity'] = float(row.NominalRatingKVA)
				cymeqxfmr[row.EquipmentId]['PrimaryVoltage'] = float(row.PrimaryVoltageKVLL)*1000.0/math.sqrt(3.0)
				cymeqxfmr[row.EquipmentId]['SecondaryVoltage'] = float(row.SecondaryVoltageKVLL)*1000.0/math.sqrt(3.0)
				if cymeqxfmr[row.EquipmentId]['PrimaryVoltage'] == cymeqxfmr[row.EquipmentId]['SecondaryVoltage']:
					cymeqxfmr[row.EquipmentId]['SecondaryVoltage'] += 0.001
				z1mag = float(row.PosSeqImpedancePercent)/100.0
				r = z1mag/math.sqrt(1+(float(row.XRRatio))**2)
				if r == 0.0:
					r = 0.000333
					x = 0.00222
				else:
					x = r*float(row.XRRatio)
				cymeqxfmr[row.EquipmentId]['impedance'] = '{:0.6f}{:+0.6f}j'.format(r, x)
	return cymeqxfmr

def _readCymePhotovoltaic(feederId, modelDir):
	cymePhotovoltaic = {}
	CYMEPHOTOVOLTAIC = { 'name': None,
						'configuration': None}
	cymphotovoltaic_db = _csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMPHOTOVOLTAIC.csv"),feederId)
	if len(cymphotovoltaic_db) == 0:
		warnings.warn("No photovoltaic information was found in CYMPHOTOVOLTAIC for feeder id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in cymphotovoltaic_db:
			row.DeviceNumber = _fixName(row.DeviceNumber)
			if row.DeviceNumber not in cymePhotovoltaic.keys():
				cymePhotovoltaic[row.DeviceNumber] = copy.deepcopy(CYMEPHOTOVOLTAIC)
				cymePhotovoltaic[row.DeviceNumber]['name'] = row.DeviceNumber
				cymePhotovoltaic[row.DeviceNumber]['configuration'] = row.EquipmentId
	return cymePhotovoltaic

def _readEqPhotovoltaic(feederId, modelDir):
	cymEqPhotovoltaic = {}
	CYMEQPHOTOVOLTAIC = {'name':None,
						  'current':4.59,
						  'voltage':17.30,
						  'efficiency':0.155}
	cymeqphotovoltaic_db = _csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMEQPHOTOVOLTAIC.csv"),feederId)
	if len(cymeqphotovoltaic_db) == 0:
		warnings.warn("No photovoltaic information was found in CYMEQPHOTOVOLTAIC for feeder id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in cymeqphotovoltaic_db:
			row.DeviceNumber = _fixName(row.EquipmentId)
			if row.DeviceNumber not in cymEqPhotovoltaic.keys():
				cymEqPhotovoltaic[row.DeviceNumber] = copy.deepcopy(CYMEQPHOTOVOLTAIC)
				cymEqPhotovoltaic[row.DeviceNumber]['name'] = row.EquipmentId
				cymEqPhotovoltaic[row.DeviceNumber]['current'] = row.MPPCurrent
				cymEqPhotovoltaic[row.DeviceNumber]['voltage'] = row.MPPVoltage
	return cymEqPhotovoltaic

def _readEqBattery(feederId, modelDir):
	cymEqBattery = {}
	CYMEQBATTERY = {
		'name': None,
		'rated_storage_energy': None,
		'max_charging_power': None,
		'max_discharging_power': None,
		'charge_efficiency':None,
		'discharge_efficiency':None
	}
	cymeqbattery_db = _csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMEQBESS.csv"),feederId)
	if len(cymeqbattery_db) == 0:
		warnings.warn("No battery information was found in CYMEQBATTERY for feeder id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in cymeqbattery_db:
			row.DeviceNumber = _fixName(row.EquipmentId)
			if row.DeviceNumber not in cymEqBattery.keys():
				cymEqBattery[row.DeviceNumber] = copy.deepcopy(CYMEQBATTERY)
				cymEqBattery[row.DeviceNumber]['name'] = row.EquipmentId
				cymEqBattery[row.DeviceNumber]['rated_storage_energy'] = float(row.RatedStorageEnergy)
				cymEqBattery[row.DeviceNumber]['max_charging_power'] = row.MaxChargingPower
				cymEqBattery[row.DeviceNumber]['max_discharging_power'] = row.MaxDischargingPower
				cymEqBattery[row.DeviceNumber]['round_trip_efficiency'] = float(row.ChargeEfficiency)/1000 * float(row.DischargeEfficiency)/1000
	return cymEqBattery

def _readCymeBattery(feederId, modelDir):
	cymeBattery = {}
	CYMEBATTERY = {
		'name': None,
		'configuration': None,
		'phase': None
	}
	cymbattery_db = _csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMBESS.csv"),feederId)
	if len(cymbattery_db) == 0:
		warnings.warn("No battery information was found in CYMBESS for feeder id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in cymbattery_db:
			row.DeviceNumber = _fixName(row.DeviceNumber)
			if row.DeviceNumber not in cymeBattery.keys():
				cymeBattery[row.DeviceNumber] = copy.deepcopy(CYMEBATTERY)
				cymeBattery[row.DeviceNumber]['name'] = row.DeviceNumber
				cymeBattery[row.DeviceNumber]['configuration'] = row.EquipmentId
				cymeBattery[row.DeviceNumber]['phase'] = row.Phase
	return cymeBattery

def _readCymeGenerator(feederId, modelDir):
	cymeGenerator = {}
	CYMEGENERATOR = {
		'name': None,
		'generation': None,
		'power_factor': None
	}
	cymgenerator_db = _csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMDGGENERATIONMODEL.csv"),feederId)
	if len(cymgenerator_db) == 0:
		warnings.warn("No generator information was found in CYMDGGENERATIONMODEL for feeder id: {:s}.".format(feederId), RuntimeWarning)
	else:
		for row in cymgenerator_db:
			row.DeviceNumber = _fixName(row.DeviceNumber)
			if row.DeviceType == '37':
				if row.DeviceNumber not in cymeGenerator.keys():
					cymeGenerator[row.DeviceNumber] = copy.deepcopy(CYMEGENERATOR)
					cymeGenerator[row.DeviceNumber]['name'] = row.DeviceNumber
					cymeGenerator[row.DeviceNumber]['generation'] = row.ActiveGeneration
					cymeGenerator[row.DeviceNumber]['power_factor'] = row.PowerFactor
	return cymeGenerator

def _find_SPCT_rating(load_str):
		spot_load = abs(complex(load_str))/1000.0 #jfk.  needs to be in kVA for transformer rating estimation
		spct_rating = [5,10,15,25,30,37.5,50,75,87.5,100,112.5,125,137.5,150,162.5,175,187.5,200,225,250,262.5,300,337.5,400,412.5,450,500,750,1000,1250,1500,2000,2500,3000,4000,5000]
		past_rating = max(spct_rating)
		for rating in spct_rating:
			if rating >= spot_load and rating < past_rating:
				past_rating = rating
		return str(past_rating)
	
def convertCymeModel(network_db, modelDir, test=False, type=1, feeder_id=None):
	conductor_data_csv = None
	dbflag = 0 
	#HACK: manual network ID detection.
	if 'Duke' in str(network_db):
		dbflag = 0
	elif 'OakPass' in str(network_db):
		dbflag= 1
	glmTree = {}  # Dictionary that will hold the feeder model for conversion to .glm format 
	regulator_sections = {}
	recloser_sections = {}
	sectionalizer_sections = {}
	switch_sections = {}
	fuse_sections = {}
	capacitor_sections = {}
	vsc_sections = {}
	threewautoxfmr_sections = {}
	transformer_sections = {}
	overheadline_sections = {}
	undergroundline_sections = {}
	sx_section = []
	reactor_sections = {}
	pv_sections = {}
	load_sections = {}
	threewxfmr_sections = {}
	battery_sections = {}
	syncgen_sections = {}
	# Open the network database file
	# net_db = _openDatabase(network_db)
	# Dumping csv's to folder
	_csvDump(str(network_db), modelDir)
	# import pdb
	# pdb.set_trace()
	# feeder_id =_csvToDictList(pJoin(modelDir,'cymeCsvDump',"CYMNETWORK.csv"),columns=['NetworkId'])
	feeder_id = _findNetworkId(pJoin(modelDir,'cymeCsvDump',"CYMNETWORK.csv"))
	# -1-CYME CYMSOURCE *********************************************************************************************************************************************************************
	cymsource, feeder_id, swingBus = _readCymeSource(feeder_id, type ,modelDir)
	# -2-CYME CYMNODE *********************************************************************************************************************************************************************
	cymnode, x_scale, y_scale = _readCymeNode(feeder_id, modelDir)
	# -3-CYME OVERHEADBYPHASE ****************************************************************************************************************************************************************
	OH_conductors, cymoverheadbyphase, ohConfigurations, uniqueOhSpacing = _readCymeOverheadByPhase(feeder_id, modelDir)
	# -4-CYME UNDERGROUNDLINE ****************************************************************************************************************************************************************
	UG_conductors, cymundergroundline = _readCymeUndergroundLine(feeder_id, modelDir)
	# -5-CYME CYMOVERHEADLINEBALANCED ****************************************************************************************************************************************************************
	cymUnbalancedOverheadLine, UOLConfigNames = _readCymeOverheadLineUnbalanced(feeder_id, modelDir)
	# -5-CYME CYMSWITCH**********************************************************************************************************************************************************************
	cymswitch = _readCymeSwitch(feeder_id, modelDir)
	# -6-CYME CYMSECTIONALIZER**********************************************************************************************************************************************************************
	cymsectionalizer = _readCymeSectionalizer(feeder_id, modelDir)        
	# -7-CYME CYMFUSE**********************************************************************************************************************************************************************
	cymfuse = _readCymeFuse(feeder_id, modelDir)
	# -8-CYME CYMRECLOSER**********************************************************************************************************************************************************************
	cymrecloser = _readCymeRecloser(feeder_id, modelDir)
	# -9-CYME CYMREGULATOR**********************************************************************************************************************************************************************
	cymregulator = _readCymeRegulator(feeder_id, modelDir)
      
	# -10-CYME CYMSHUNTCAPACITOR**********************************************************************************************************************************************************************
	cymshuntcapacitor = _readCymeShuntCapacitor(feeder_id, modelDir)
	# -11-CYME CYMCUSTOMERLOAD**********************************************************************************************************************************************************************
	cymcustomerload = _readCymeCustomerLoad(feeder_id, modelDir)
	# -12-CYME CYMSECTION ****************************************************************************************************************************************************************
	cymsection = _readCymeSection(feeder_id, modelDir)
	for section in cymsection.keys():
		fromNode = cymsection[section]['from']
		toNode = cymsection[section]['to']
		if fromNode in cymnode.keys():
			cymsection[section]['fromX'] = cymnode[fromNode]['latitude']
			cymsection[section]['fromY'] = cymnode[fromNode]['longitude']
		else:
			cymsection[section]['fromX'] = '0'
			cymsection[section]['fromY'] = '800'
		if toNode in cymnode.keys():
			cymsection[section]['toX'] = cymnode[toNode]['latitude']
			cymsection[section]['toY'] = cymnode[toNode]['longitude']
		else:
			cymsection[section]['toX'] = '0'
			cymsection[section]['toY'] = '800'
	# -13-CYME CYMSECTIONDEVICE ****************************************************************************************************************************************************************
	cymsectiondevice = _readCymeSectionDevice(feeder_id, modelDir) 
	# OVERHEAD LINES
	cymoverheadline, lineIds = _readCymeOverheadLine(feeder_id, modelDir)
	# OVERHEAD LINE CONFIGS
	cymeqoverheadline, spacingIds = _readCymeQOverheadLine(feeder_id, modelDir)
	# PV
	cymphotovoltaic = _readCymePhotovoltaic(feeder_id,modelDir)
	# PV CONFIGS
	cymeqphotovoltaic = _readEqPhotovoltaic(feeder_id,modelDir)
	try:
		# BATTERY
		cymbattery = _readCymeBattery(feeder_id, modelDir)
		# BATTERY CONFIGS
		cymeqbattery = _readEqBattery(feeder_id,modelDir)
	except:
		pass #HACK: generator failure.
	try:
		# GENERATOR
		cymgenerator = _readCymeGenerator(feeder_id, modelDir)
	except:
		pass #HACK: generator failure.
	# Check that the section actually is a device.
	for link in cymsection.keys():
		link_exists = 0
		for device in cymsectiondevice.keys():
			if cymsectiondevice[device]['section_name'] == link:
				link_exists = 1
		if link_exists == 0:
			cymsection[link]['connector'] = ''
			warnings.warn("There is no device associated with section:{:s} in network database:{:s}. This will be modeled as a switch.".format(link, network_db), RuntimeWarning)
	for link in cymsection.keys():
		if 'connector' in cymsection[link].keys():
			cymsectiondevice[link] = { 'name' : link,
						'device_type' : 13,
						'section_name' : link,
						'location' : 0}
			cymswitch[link] = { 'name' : link,            # Information structure for each object found in CYMSWITCH
				  'equipment_name' : None,
				  'status' : 1}
			del cymsection[link]['connector']
	# Remove islands from the network database
	fromNodes = []
	toNodes = []
	cleanToNodes = []
	for link in cymsection.keys():
		if 'from' in cymsection[link].keys():
			if cymsection[link]['from'] not in fromNodes:
				fromNodes.append(cymsection[link]['from'])
			if cymsection[link]['to'] not in toNodes:
				toNodes.append(cymsection[link]['to'])
				cleanToNodes.append(cymsection[link]['to'])
	islandNodes = []
	for node in fromNodes:
		if node not in toNodes and node != swingBus and node not in islandNodes:
			islandNodes.append(node)
	islands = 0
	nislands = len(islandNodes)
	while nislands != islands:
		islands = len(islandNodes)
		for link in cymsection.keys():
			if 'from' in cymsection[link].keys():
				if cymsection[link]['from'] in islandNodes and cymsection[link]['to'] not in islandNodes:
					islandNodes.append(cymsection[link]['to'])
		nislands = len(islandNodes)
	deleteSections = []
	for node in islandNodes:
		for link in cymsection.keys():
			if (node == cymsection[link]['from'] or node == cymsection[link]['to']) and link not in deleteSections:
				deleteSections.append(link)
	# for section in deleteSections:
	#     del cymsection[section]
	# for device in cymsectiondevice.keys():
	#     if cymsectiondevice[device]['section_name'] in deleteSections:
	#         del cymsectiondevice[device]
	# Group each type of device.
	for device in cymsectiondevice.keys():
		if cymsectiondevice[device]['device_type'] == 1:
			undergroundline_sections[cymsectiondevice[device]['section_name']] = device
		elif cymsectiondevice[device]['device_type'] == 3 or cymsectiondevice[device]['device_type'] == 2:
			overheadline_sections[cymsectiondevice[device]['section_name']] = device
		elif cymsectiondevice[device]['device_type'] == 4:
			regulator_sections[cymsectiondevice[device]['section_name']] = device
		elif cymsectiondevice[device]['device_type'] == 10: 
			recloser_sections[cymsectiondevice[device]['section_name']] = device
		elif cymsectiondevice[device]['device_type'] == 12:
			sectionalizer_sections[cymsectiondevice[device]['section_name']] = device
		elif cymsectiondevice[device]['device_type'] == 13:
			if cymsectiondevice[device]['section_name'] not in switch_sections.keys():
				switch_sections[cymsectiondevice[device]['section_name']] = [device] #jfk. could use default dict to make this cleaner
			else:
				switch_sections[cymsectiondevice[device]['section_name']].append(device)
			# switch_sections[cymsectiondevice[device]['section_name']] = device #sometimes have two switches on a section!  this overwrite the first!
		elif cymsectiondevice[device]['device_type'] == 14:
			fuse_sections[cymsectiondevice[device]['section_name']] = device
		elif cymsectiondevice[device]['device_type'] == 16:
			# sx_section.append(cymsectiondevice[device]['section_name']) #this was not needed for PECO files
			reactor_sections[cymsectiondevice[device]['section_name']] = device
		elif cymsectiondevice[device]['device_type'] == 17:
			capacitor_sections[cymsectiondevice[device]['section_name']] = device
		elif cymsectiondevice[device]['device_type'] == 20:
			load_sections[cymsectiondevice[device]['section_name']] = device
		elif cymsectiondevice[device]['device_type'] == 37:
			syncgen_sections[cymsectiondevice[device]['section_name']] = device
		elif cymsectiondevice[device]['device_type'] == 45:
			if cymsectiondevice[device]['section_name'] not in pv_sections.keys():
				pv_sections[cymsectiondevice[device]['section_name']] = [device] #jfk
			else:
				pv_sections[cymsectiondevice[device]['section_name']].append(device)
		elif cymsectiondevice[device]['device_type'] == 47 or cymsectiondevice[device]['device_type'] == 5: #jfk.  added check for 5, another transformer device
			transformer_sections[cymsectiondevice[device]['section_name']] = device
		elif cymsectiondevice[device]['device_type'] == 48:
			if dbflag == 0:
				threewautoxfmr_sections[cymsectiondevice[device]['section_name']] = device
			elif dbflag == 1:
				threewxfmr_sections[cymsectiondevice[device]['section_name']] = device
		elif cymsectiondevice[device]['device_type'] == 80:
			battery_sections[cymsectiondevice[device]['section_name']] = device
	# find the parent of capacitors, loads, and pv
	for x in [capacitor_sections, load_sections, pv_sections, syncgen_sections, battery_sections]:
		if len(x) > 0:
			_findParents(cymsection, cymsectiondevice, x)
	# split out fuses, regulators, transformers, switches, reclosers, and sectionalizers from the lines.
	# mj debug: check these phases
	for x in [fuse_sections, regulator_sections, threewxfmr_sections, threewautoxfmr_sections, transformer_sections, switch_sections, recloser_sections, sectionalizer_sections, reactor_sections]:
		if len(x) > 0:
			_splitLinkObjects(cymsection, cymsectiondevice, x, overheadline_sections, undergroundline_sections)          
	# -14-CYME CYMTRANSFORMER**********************************************************************************************************************************************************************
	cymxfmr = _readCymeTransformer(feeder_id, modelDir)
	# -15-CYME CYMTHREEWINDINGTRANSFORMER******************************************************************************************************************************************************************************************
	cym3wxfmr = _readCymeThreeWindingTransformer(feeder_id, modelDir)
	# -16-CYME CYMEQCONDUCTOR**********************************************************************************************************************************************************************
	cymeqconductor = _readEqConductor(feeder_id, modelDir)
	# -17-CYME CYMEQCONDUCTOR**********************************************************************************************************************************************************************
	cymeqoverheadlineunbalanced = _readEqOverheadLineUnbalanced(feeder_id, modelDir)
	# -17-CYME CYMEQGEOMETRICALARRANGEMENT**********************************************************************************************************************************************************************
	if dbflag == 0:
		cymeqgeometricalarrangement = _readEqGeometricalArrangement(feeder_id, modelDir) 
	elif dbflag == 1:
		cymeqgeometricalarrangement = _readEqAvgGeometricalArrangement(feeder_id, modelDir)
	# -18-CYME convertCymeModelXLSX Sheet**********************************************************************************************************************************************************************
	cymcsvundergroundcable = _readUgConfiguration(feeder_id, modelDir)
	# -19-CYME CYMEQREGULATOR**********************************************************************************************************************************************************************
	cymeqregulator = _readEqRegulator(feeder_id, modelDir)
	# -20-CYME CYMEQTHREEWINDAUTOTRANSFORMER**********************************************************************************************************************************************************************
	cymeq3wautoxfmr = _readEqThreeWAutoXfmr(feeder_id, modelDir)
	# -21-CYME CYMEQAUTOTRANSFORMER**********************************************************************************************************************************************************************
	cymeqautoxfmr = _readEqAutoXfmr(feeder_id, modelDir)
	# -22-CYME CYME REACTORS********************************************************************************************
	cymreactor, reactorIds =_readCymeReactors(feeder_id, modelDir)
	# -23-CYME CYMEQREACTORS********************************************************************************************
	cymeqreactor =_readEqReactors(feeder_id, modelDir)
	# -24-CYME CYMEQTRANSFORMER********************************************************************************************
	cymeqxfmr =_readEqXfmr(feeder_id, modelDir)
	# Check number of sources
	meters = {}
	if len(cymsource) > 1:
		print"There is more than one swing bus for feeder_id ", feeder_id, "\n"      
	for x in cymsource.keys():
		meters[x] = { 'object' : 'meter',
						 'name' : '{:s}'.format(cymsource[x]['name']),
						 # 'bustype' : 'SWING',
						 'nominal_voltage' : cymsource[x]['nominal_voltage'],
						 'latitude' : cymnode[x]['latitude'],
						 'longitude' : cymnode[x]['longitude']}
		feeder_VLN = cymsource[x]['nominal_voltage']
	# Check for parallel links and islands
	fromTo = []
	fromNodes = []
	toNodes = []
	parallelLinks = []
	for link in cymsection.keys():
		if 'from' in cymsection[link].keys() and 'to' in cymsection[link].keys():
			if [cymsection[link]['from'], cymsection[link]['to']] in fromTo or [cymsection[link]['to'], cymsection[link]['from']] in fromTo:
				for key in cymsectiondevice.keys():
					if cymsectiondevice[key]['section_name'] == link:
						parallelLinks.append(key)
			else:
				fromTo.append([cymsection[link]['from'], cymsection[link]['to']])
			if cymsection[link]['from'] not in fromNodes:
				fromNodes.append(cymsection[link]['from'])
			if cymsection[link]['to'] not in toNodes:
				toNodes.append(cymsection[link]['to'])
	# islandNodes = []
	# for node in fromNodes:
	#     if node not in toNodes and node != swingBus and node not in islandNodes:
	#         islandNodes.append(node)
	# for node in islandNodes:
	#     if node != swingBus:
	#         print "Feeder islanded\n"            
	# Pass from, to, and phase information from cymsection to cymsectiondevice
	nodes = {}
	for device in cymsectiondevice.keys():
		if 'parent' not in cymsectiondevice[device].keys():
			cymsectiondevice[device]['from'] = cymsection[cymsectiondevice[device]['section_name']]['from']
			cymsectiondevice[device]['to'] = cymsection[cymsectiondevice[device]['section_name']]['to']
			cymsectiondevice[device]['phases'] = cymsection[cymsectiondevice[device]['section_name']]['phases']
			cymsectiondevice[device]['fromLatitude'] = cymsection[cymsectiondevice[device]['section_name']]['fromX']
			cymsectiondevice[device]['fromLongitude'] = cymsection[cymsectiondevice[device]['section_name']]['fromY']
			cymsectiondevice[device]['toLatitude'] = cymsection[cymsectiondevice[device]['section_name']]['toX']
			cymsectiondevice[device]['toLongitude'] = cymsection[cymsectiondevice[device]['section_name']]['toY']
		# Create all the node dictionaries
			if cymsectiondevice[device]['from'] not in nodes.keys() and cymsectiondevice[device]['from'] != swingBus:
				nodes[cymsectiondevice[device]['from']] = {'object' : 'node',
				'name' : cymsectiondevice[device]['from'],
				'phases' : cymsectiondevice[device]['phases'],
				'nominal_voltage' : str(feeder_VLN),
				'latitude' : cymsectiondevice[device]['fromLatitude'],
				'longitude' : cymsectiondevice[device]['fromLongitude']}
			if cymsectiondevice[device]['to'] not in nodes.keys() and cymsectiondevice[device]['to'] != swingBus:
				nodes[cymsectiondevice[device]['to']] = {'object' : 'node',
				'name' : cymsectiondevice[device]['to'],
				'phases' : cymsectiondevice[device]['phases'],
				'nominal_voltage' : str(feeder_VLN),
				'latitude' : cymsectiondevice[device]['toLatitude'],
				'longitude' : cymsectiondevice[device]['toLongitude']}
		else:
			cymsectiondevice[device]['fromLatitude'] = cymsection[cymsectiondevice[device]['section_name']]['fromX']
			cymsectiondevice[device]['fromLongitude'] = cymsection[cymsectiondevice[device]['section_name']]['fromY']
			cymsectiondevice[device]['toLatitude'] = cymsection[cymsectiondevice[device]['section_name']]['toX']
			cymsectiondevice[device]['toLongitude'] = cymsection[cymsectiondevice[device]['section_name']]['toY']
			if cymsectiondevice[device]['parent'] not in nodes.keys() and cymsectiondevice[device]['parent'] != swingBus:
				nodes[cymsectiondevice[device]['parent']] = {'object' : 'node',
					'name' : cymsectiondevice[device]['parent'],
					'phases' : cymsectiondevice[device]['phases'],
					'nominal_voltage' : str(feeder_VLN)}
				if cymsectiondevice[device]['location'] == 2:
					nodes[cymsectiondevice[device]['parent']]['latitude'] = cymsectiondevice[device]['toLatitude']
					nodes[cymsectiondevice[device]['parent']]['longitude'] = cymsectiondevice[device]['toLongitude']
				else:
					nodes[cymsectiondevice[device]['parent']]['latitude'] = cymsectiondevice[device]['fromLatitude']
					nodes[cymsectiondevice[device]['parent']]['longitude'] = cymsectiondevice[device]['fromLongitude']
	# Create overhead line conductor dictionaries
	ohl_conds = {}
        print "REACHED"
	for olc in OH_conductors:
		if olc in cymeqconductor.keys():
			if olc not in ohl_conds.keys():
				ohl_conds[olc] = {'object' : 'overhead_line_conductor',
					'name' : olc,
					'resistance' : '{:0.6f}'.format(cymeqconductor[olc]['resistance']),
					'geometric_mean_radius' : '{:0.6f}'.format(cymeqconductor[olc]['geometric_mean_radius'])}
		else:
			print "There is no conductor spec for ", olc, " in the equipment database provided.\n" 
	for olc in cymeqconductor:
		if olc in cymeqconductor.keys():
			if olc not in ohl_conds.keys():
				ohl_conds[olc] = {'object' : 'overhead_line_conductor',
					'name' : olc,
					'resistance' : '{:0.6f}'.format(cymeqconductor[olc]['resistance']),
					'geometric_mean_radius' : '{:0.6f}'.format(cymeqconductor[olc]['geometric_mean_radius'])}
		else:
			print "There is no conductor spec for ", olc, " in the equipment database provided.\n" 
	ohl_configs = {}
	for ohlc in cymeqoverheadline:
		if ohlc in lineIds:
			if ohlc not in ohl_configs.keys():
				ohl_configs[ohlc] = {'object' : 'line_configuration',
					'name': ohlc+'conf',
					'spacing': cymeqoverheadline[ohlc]['spacing']+'ohsps',
					'conductor_A': cymeqoverheadline[ohlc]['configuration'],
					'conductor_B': cymeqoverheadline[ohlc]['configuration'],
					'conductor_C': cymeqoverheadline[ohlc]['configuration'],
					'conductor_N': cymeqoverheadline[ohlc]['conductor_N']}
	ohl_spcs = {}
	# Create overhead line spacing dictionaries
	for ols in uniqueOhSpacing:
		if ols in cymeqgeometricalarrangement.keys():
			if ols not in ohl_spcs.keys():
				ohl_spcs[ols] = {'object' : 'line_spacing',
					'name' : ols,
					'distance_AB' : '{:0.6f}'.format(cymeqgeometricalarrangement[ols]['distance_AB']),
					'distance_AC' : '{:0.6f}'.format(cymeqgeometricalarrangement[ols]['distance_AC']),
					'distance_AN' : '{:0.6f}'.format(cymeqgeometricalarrangement[ols]['distance_AN']),
					'distance_BC' : '{:0.6f}'.format(cymeqgeometricalarrangement[ols]['distance_BC']),
					'distance_BN' : '{:0.6f}'.format(cymeqgeometricalarrangement[ols]['distance_BN']),
					'distance_CN' : '{:0.6f}'.format(cymeqgeometricalarrangement[ols]['distance_CN'])}
		else:
			print "There is no line spacing spec for ", ols, "in the equipment database provided.\n" 
	
	for ols in spacingIds:
		if ols in cymeqgeometricalarrangement.keys():
			if ols not in ohl_spcs.keys():
				ohl_spcs[ols] = {'object' : 'line_spacing',
								'name' : ols+'ohsps',
								'distance_AB' : '{:0.6f}'.format(cymeqgeometricalarrangement[ols]['distance_AB']),
								'distance_AC' : '{:0.6f}'.format(cymeqgeometricalarrangement[ols]['distance_AC']),
								'distance_AN' : '{:0.6f}'.format(cymeqgeometricalarrangement[ols]['distance_AN']),
								'distance_BC' : '{:0.6f}'.format(cymeqgeometricalarrangement[ols]['distance_BC']),
								'distance_BN' : '{:0.6f}'.format(cymeqgeometricalarrangement[ols]['distance_BN']),
								'distance_CN' : '{:0.6f}'.format(cymeqgeometricalarrangement[ols]['distance_CN'])}
	# Create overhead line configuration dictionaries
	ohl_cfgs = {}
	ohl_neutral = []
	for olcfg in ohConfigurations:
		if olcfg not in ohl_cfgs.keys():
			ohl_cfgs[olcfg] = copy.deepcopy(ohConfigurations[olcfg])
			ohl_cfgs[olcfg]['name'] = olcfg
			ohl_cfgs[olcfg]['object'] = 'line_configuration'
			if 'conductor_N' in ohl_cfgs[olcfg].keys():
				ohl_neutral.append(olcfg)
	for olcfg in UOLConfigNames:
		if olcfg in cymeqoverheadlineunbalanced.keys():
			if olcfg not in ohl_cfgs.keys():
				ohl_cfgs[olcfg] = copy.deepcopy(cymeqoverheadlineunbalanced[olcfg])
		else:
			print "There is no overhead line configuration for", olcfg, " in the equipment database provided."
			
	# Create overhead line dictionaries
	ohls = {}
	for ohl in cymsectiondevice.keys():
		if cymsectiondevice[ohl]['device_type'] == 3:
			if ohl not in cymoverheadbyphase.keys():
				print "There is no line spec for ", ohl, " in the network database provided.\n"                  
			elif ohl not in ohls.keys():
				if ohl not in parallelLinks:
					ohls[ohl] = {'object' : 'overhead_line',
											'name' : ohl,
											'phases' : cymsectiondevice[ohl]['phases'],
											'from' :  cymsectiondevice[ohl]['from'],
											'to' :  cymsectiondevice[ohl]['to'],
											'length' :  '{:0.6f}'.format(cymoverheadbyphase[ohl]['length']),
											'configuration' : cymoverheadbyphase[ohl]['configuration']}
				else: 
					ohls[ohl + 'par1'] = {'object' : 'overhead_line',
											'name' : ohl + 'par1',
											'phases' : cymsectiondevice[ohl]['phases'],
											'from' :  cymsectiondevice[ohl]['from'],
											'to' :  ohl + 'parNode',
											'length' :  '{:0.6f}'.format(cymoverheadbyphase[ohl]['length']/2.0),
											'configuration' : cymoverheadbyphase[ohl]['configuration']}
					ohls[ohl + 'par2'] = {'object' : 'overhead_line',
											'name' : ohl + 'par2',
											'phases' : cymsectiondevice[ohl]['phases'],
											'from' :  ohl + 'parNode',
											'to' :  cymsectiondevice[ohl]['to'],
											'length' :  '{:0.6f}'.format(cymoverheadbyphase[ohl]['length']/2.0),
											'configuration' : cymoverheadbyphase[ohl]['configuration']}
					nodes[ohl + 'parNode'] = {'object' : 'node',
																	'name' : ohl + 'parNode',
																	'phases' : cymsectiondevice[ohl]['phases'],
																	'nominal_voltage' : str(feeder_VLN),
																	'latitude' : str((float(cymsectiondevice[ohl]['fromLatitude']) + float(cymsectiondevice[ohl]['toLatitude']))/2.0),
																	'longitude' : str((float(cymsectiondevice[ohl]['fromLongitude']) + float(cymsectiondevice[ohl]['toLongitude']))/2.0)}
		if cymsectiondevice[ohl]['device_type'] == 2:
			if ohl not in cymoverheadline.keys():
				print "There is no line spec for ", oh1, " in the network database provided.\n"
			elif ohl not in ohls.keys():
				if ohl not in parallelLinks:
					   ohls[ohl] = {'object' : 'overhead_line',
											'name' : ohl,
											'phases' : cymsectiondevice[ohl]['phases'],
											'from' :  cymsectiondevice[ohl]['from'],
											'to' :  cymsectiondevice[ohl]['to'],
											'length' :  '{:0.6f}'.format(cymoverheadline[ohl]['length']),
											'configuration' : cymoverheadline[ohl]['configuration']+'conf'}
		elif cymsectiondevice[ohl]['device_type'] == 23:
			if ohl not in cymUnbalancedOverheadLine.keys():
				print "There is no line spec for ", oh1, " in the network database provided.\n"  
			elif ohl not in ohls.keys():
				if ohl not in parallelLinks:
					ohls[ohl] = {'object' : 'overhead_line',
											'name' : ohl,
											'phases' : cymsectiondevice[ohl]['phases'],
											'from' :  cymsectiondevice[ohl]['from'],
											'to' :  cymsectiondevice[ohl]['to'],
											'length' :  '{:0.6f}'.format(cymUnbalancedOverheadLine[ohl]['length']),
											'configuration' : cymUnbalancedOverheadLine[ohl]['configuration']}
				else: 
					ohls[ohl + 'par1'] = {'object' : 'overhead_line',
											'name' : ohl + 'par1',
											'phases' : cymsectiondevice[ohl]['phases'],
											'from' :  cymsectiondevice[ohl]['from'],
											'to' :  ohl + 'parNode',
											'length' :  '{:0.6f}'.format(cymUnbalancedOverheadLine[ohl]['length']/2.0),
											'configuration' : cymUnbalancedOverheadLine[ohl]['configuration']}
					ohls[ohl + 'par2'] = {'object' : 'overhead_line',
											'name' : ohl + 'par2',
											'phases' : cymsectiondevice[ohl]['phases'],
											'from' :  ohl + 'parNode',
											'to' :  cymsectiondevice[ohl]['to'],
											'length' :  '{:0.6f}'.format(cymUnbalancedOverheadLine[ohl]['length']/2.0),
											'configuration' : cymUnbalancedOverheadLine[ohl]['configuration']}
					nodes[ohl + 'parNode'] = {'object' : 'node',
																	'name' : ohl + 'parNode',
																	'phases' : cymsectiondevice[ohl]['phases'],
																	'nominal_voltage' : str(feeder_VLN),
																	'latitude' : str((float(cymsectiondevice[ohl]['fromLatitude']) + float(cymsectiondevice[ohl]['toLatitude']))/2.0),
																	'longitude' : str((float(cymsectiondevice[ohl]['fromLongitude']) + float(cymsectiondevice[ohl]['toLongitude']))/2.0)}
				
	# Create underground line conductor, and spacing dictionaries
	ugl_conds = {}
	ugl_sps = {}
	for ulc in UG_conductors:
		if ulc in cymcsvundergroundcable.keys():
			if ulc + 'cond' not in ugl_conds.keys():
				ugl_conds[ulc + 'cond'] = {'object' : 'underground_line_conductor',
																'name' : ulc + 'cond',
																'conductor_resistance' : cymcsvundergroundcable[ulc]['conductor_resistance'],
																'neutral_gmr' : cymcsvundergroundcable[ulc]['neutral_gmr'],
																'outer_diameter' : cymcsvundergroundcable[ulc]['outer_diameter'],
																'neutral_strands' : cymcsvundergroundcable[ulc]['neutral_strands'],
																'neutral_resistance' : cymcsvundergroundcable[ulc]['neutral_resistance'],
																'neutral_diameter' : cymcsvundergroundcable[ulc]['neutral_diameter'],
																'conductor_diameter' : cymcsvundergroundcable[ulc]['conductor_diameter'],
																'conductor_gmr' : cymcsvundergroundcable[ulc]['conductor_gmr']}
				if ulc + 'sps' not in ugl_sps.keys():
					ugl_sps[ulc + 'sps'] = {'object' : 'line_spacing',
															'name' : ulc + 'sps',
															'distance_AB' : cymcsvundergroundcable[ulc]['distance_AB'],
															'distance_AC' : cymcsvundergroundcable[ulc]['distance_AC'],
															'distance_BC' : cymcsvundergroundcable[ulc]['distance_BC']}
		else:
			print "Runtimerror: No configuration spec for {:s} in the underground csv file provided.", ulc
	# Creat Underground line configuration, and link objects.
	ugl_cfgs = {}
	ugls = {}
	for ugl in cymsectiondevice.keys():
		if cymsectiondevice[ugl]['device_type'] == 1:
			ph = cymsectiondevice[ugl]['phases'].replace('N', '')
			if ugl not in cymundergroundline.keys():
				print "There is no line spec for ", ugl, " in the network database provided.\n"
			else:
				phs = 0
				if 'A' in ph:
					phs += 1
				if 'B' in ph:
					phs += 2
				if 'C' in ph:
					phs += 4
				if phs == 1:
					config_name = cymundergroundline[ugl]['cable_id'] + 'phA'
				elif phs == 2:
					config_name = cymundergroundline[ugl]['cable_id'] + 'phB'
				elif phs == 4:
					config_name = cymundergroundline[ugl]['cable_id'] + 'phC'
				elif phs == 3:
					config_name = cymundergroundline[ugl]['cable_id'] + 'phAB'
				elif phs == 5:
					config_name = cymundergroundline[ugl]['cable_id'] + 'phAC'
				elif phs == 6:
					config_name = cymundergroundline[ugl]['cable_id'] + 'phBC'
				elif phs == 7:
					config_name = cymundergroundline[ugl]['cable_id'] + 'phABC'
				if config_name not in ugl_cfgs.keys():
					cableid = cymundergroundline[ugl]['cable_id']
					ugl_cfgs[config_name] = {'object' : 'line_configuration',
																'name' : config_name,
																'spacing' : cymundergroundline[ugl]['cable_id'] + 'sps', #jfk
																'z11': cymcsvundergroundcable[cableid]['z11'],
																'z12': cymcsvundergroundcable[cableid]['z12'],
																'z13': cymcsvundergroundcable[cableid]['z13'],
																'z21': cymcsvundergroundcable[cableid]['z21'],
																'z22': cymcsvundergroundcable[cableid]['z22'],
																'z23': cymcsvundergroundcable[cableid]['z23'],
																'z31': cymcsvundergroundcable[cableid]['z31'],
																'z32': cymcsvundergroundcable[cableid]['z32'],
																'z33': cymcsvundergroundcable[cableid]['z33']}
					for phase in ph:
						if phase != 'D' or phase != 'N':
							ugl_cfgs[config_name]['conductor_{:s}'.format(phase)] = cymundergroundline[ugl]['cable_id'] + 'cond'
				if ugl not in ugls.keys():
					if ugl not in parallelLinks:
						ugls[ugl] = {'object' : 'underground_line',
												'name' : ugl,
												'phases' : cymsectiondevice[ugl]['phases'],
												'from' :  cymsectiondevice[ugl]['from'],
												'to' :  cymsectiondevice[ugl]['to'],
												'length' :  '{:0.6f}'.format(cymundergroundline[ugl]['length']),
												'configuration' : config_name}
					else: 
						ugls[ugl + 'par1'] = {'object' : 'underground_line',
												'name' : ugl + 'par1',
												'phases' : cymsectiondevice[ugl]['phases'],
												'from' :  cymsectiondevice[ugl]['from'],
												'to' :  ugl + 'parNode',
												'length' :  '{:0.6f}'.format(cymundergroundline[ugl]['length']/2.0),
												'configuration' : config_name}
						ugls[ugl + 'par2'] = {'object' : 'underground_line',
												'name' : ugl + 'par2',
												'phases' : cymsectiondevice[ugl]['phases'],
												'from' :  ugl + 'parNode',
												'to' :  cymsectiondevice[ugl]['to'],
												'length' :  '{:0.6f}'.format(cymundergroundline[ugl]['length']/2.0),
												'configuration' : config_name}
						nodes[ugl + 'parNode'] = {'object' : 'node',
																		'name' : ugl + 'parNode',
																		'phases' : cymsectiondevice[ugl]['phases'],
																		'nominal_voltage' : str(feeder_VLN),
																		'latitude' : str((float(cymsectiondevice[ugl]['fromX']) + float(cymsectiondevice[ugl]['toX']))/2.0),
																		'longitude' : str((float(cymsectiondevice[ugl]['fromY']) + float(cymsectiondevice[ugl]['toY']))/2.0)}      
	# Create switch dictionaries
	swObjs = {}
	for swObj in cymsectiondevice.keys():
		if cymsectiondevice[swObj]['device_type'] == 13:
			# print swObj
			if swObj not in cymswitch.keys():
				print "There is no switch spec for  ", swObj, " in the network database provided.\n"  
			elif swObj not in swObjs.keys():
				swObjs[swObj] = {'object' : 'switch',
												'name' : swObj,
												'phases' : cymsectiondevice[swObj]['phases'].replace('N', ''),
												'from' : cymsectiondevice[swObj]['from'],
												'to' : cymsectiondevice[swObj]['to'],
												'operating_mode' : 'BANKED'}
				if cymswitch[swObj]['status'] == 0:
					status = 'OPEN'#jfk.  This was CLOSED.  Must have been a typo?
				else:
					status = 'CLOSED'
				for phase in swObjs[swObj]['phases']:
					swObjs[swObj]['phase_{:s}_state'.format(phase)] = status
	# Create recloser dictionaries
	rcls = {}
	for rcl in cymsectiondevice.keys():
		if cymsectiondevice[rcl]['device_type'] == 10:
			if rcl not in cymrecloser.keys():
				print "There is no recloster spec for ", rc1, " in the network database provided.\n"  
			elif rcl not in rcls.keys():
				rcls[rcl] = {'object' : 'recloser',
										'name' : rcl,
										'phases' : cymsectiondevice[rcl]['phases'].replace('N', ''),
										'from' : cymsectiondevice[rcl]['from'],
										'to' : cymsectiondevice[rcl]['to'],
										'operating_mode' : 'BANKED'}
				if cymrecloser[rcl]['status'] == 0:
					status = 'OPEN' # was 'CLOSED'  #jfk.  Mistake seemed intentional. Maybe it was just a typo?
				else:
					status = 'CLOSED'
				for phase in rcls[rcl]['phases']:
					rcls[rcl]['phase_{:s}_state'.format(phase)] = status
	# Create sectionalizer dictionaries
	sxnlrs = {}
	for sxnlr in cymsectiondevice.keys():
		if cymsectiondevice[sxnlr]['device_type'] == 12:
			if sxnlr not in cymsectionalizer.keys():
				print "There is no sectionalizer spec for ", sxnlr, " in the network database provided.\n"  
			elif sxnlr not in sxnlrs.keys():
				sxnlrs[sxnlr] = {'object' : 'sectionalizer',
										'name' : sxnlr,
										'phases' : cymsectiondevice[sxnlr]['phases'].replace('N', ''),
										'from' : cymsectiondevice[sxnlr]['from'],
										'to' : cymsectiondevice[sxnlr]['to'],
										'operating_mode' : 'BANKED'}
				if cymsectionalizer[sxnlr]['status'] == 0:
					status = 'OPEN' # 'CLOSED' #jfk
				else:
					status = 'CLOSED'
				for phase in sxnlrs[sxnlr]['phases']:
					sxnlrs[sxnlr]['phase_{:s}_state'.format(phase)] = status
	# Create fuse dictionaries
	fuses = {}
	for fuse in cymsectiondevice.keys():
		if cymsectiondevice[fuse]['device_type'] == 14:
			if fuse not in cymfuse.keys():
				print "There is no fuse spec for ", fuse, " in the network database provided.\n"                
			elif fuse not in fuses.keys():
				fuses[fuse] = {'object' : 'fuse',
										'name' : fuse,
										'phases' : cymsectiondevice[fuse]['phases'].replace('N', ''),
										'from' : cymsectiondevice[fuse]['from'],
										'to' : cymsectiondevice[fuse]['to'],
										'repair_dist_type' : 'EXPONENTIAL',
										'mean_replacement_time' : '3600',
										'current_limit' : '9999'}
				if cymfuse[fuse]['status'] == 0:
					status = 'GOOD'
				else:
					status = 'GOOD'
				for phase in fuses[fuse]['phases']:
					fuses[fuse]['phase_{:s}_status'.format(phase)] = status

	#jfk.  added all this reactor code
	reactors = {}
	for reactor in cymsectiondevice.keys():
		if cymsectiondevice[reactor]['device_type'] == 16:
			if reactor not in cymreactor.keys():
				print "There is no reactor spec for ", reactor, " in the network database provice. \n"
			elif reactor not in reactors.keys():
				reactors[reactor] = {'object' : 'series_reactor',
										'name' : reactor,
										'phases' : cymsectiondevice[reactor]['phases'].replace('N', ''),
										'from' : cymsectiondevice[reactor]['from'],
										'to' : cymsectiondevice[reactor]['to']}
				equipmentId = cymreactor[reactor]['configuration']
				Zohms = float(cymeqreactor[equipmentId]['reactance'])
				for ph in reactors[reactor]['phases']:
					reactors[reactor]['phase_' + ph + '_reactance'] = '{:0.6f}'.format(Zohms)

	# Create capacitor dictionaries
	caps = {}
	for cap in cymsectiondevice.keys():
		if cymsectiondevice[cap]['device_type'] == 17:
			if cap not in cymshuntcapacitor.keys():               
				print "There is no capacitor spec for ", cap, " in the network database provided.\n"
			elif cap not in caps.keys():
				caps[cap] = {'object' : 'capacitor',
										'name' : cap,
										'phases' : cymsectiondevice[cap]['phases'],
							 			'phases_connected' : cymsectiondevice[cap]['phases'],#jfk
										'parent' : cymsectiondevice[cap]['parent'],
										# 'control_level' : 'INDIVIDUAL', #jfk
										'control' : cymshuntcapacitor[cap]['control'],#'MANUAL',
										# 'cap_nominal_voltage' : str(feeder_VLN),
							 			'nominal_voltage': cymshuntcapacitor[cap]['kV_line_neutral'],
										'time_delay' : '2',
										'dwell_time' : '3',
										'latitude' : str(float(nodes[cymsectiondevice[cap]['parent']]['latitude']) + random.uniform(-5, 5)),
										'longitude' : str(float(nodes[cymsectiondevice[cap]['parent']]['longitude']) + random.uniform(-5, 5))}

				#This needs to be expanded for other control types too.
				if caps[cap]['control'] == 'VOLT':
					caps[cap]['remote_sense'] = 'n' + str(cymshuntcapacitor[cap]['remote_sense'])#jfk.  hacky.  have to add 'n' because it's added later to nodes.
					caps[cap]['voltage_set_high'] =str(cymshuntcapacitor[cap]['voltage_set_high']*(1/120.0)*float(feeder_VLN))
					caps[cap]['voltage_set_low'] = str(cymshuntcapacitor[cap]['voltage_set_low']*(1/120.0)*float(feeder_VLN))
					caps[cap]['pt_phase'] = cymshuntcapacitor[cap]['pt_phase']
					caps[cap]['control_level'] = cymshuntcapacitor[cap]['control_level']
					for phase in caps[cap]['phases']:
						if phase not in ['N', 'D']:
							caps[cap]['capacitor_{:s}'.format(phase)] = str(cymshuntcapacitor[cap]['capacitor_{:s}'.format(phase)])


				if cymshuntcapacitor[cap]['status'] == '1':
					status = 'OPEN'
				else:
					status = 'CLOSED'
				for phase in caps[cap]['phases']:
					if phase not in ['N', 'D']:
						caps[cap]['switch{:s}'.format(phase)] = status
						caps[cap]['capacitor_{:s}'.format(phase)] = str(cymshuntcapacitor[cap]['capacitor_{:s}'.format(phase)])
	# Create load dictionaries
	loads = {}
	spct_cfgs ={}
	spcts = {}
	tpns = {}
	tpms = {}
	loadNames = []
	for load in cymsectiondevice.keys():
		if cymsectiondevice[load]['device_type'] == 20:
			if load not in cymcustomerload.keys():
				print "There is no load spec for ", load, " in the network database provided.\n"
			elif load not in loads.keys() and cymcustomerload[load]['load_class'] == 'commercial':
				loads[load] = {'object' : 'load',
										'name' : load,
										'phases' : cymsectiondevice[load]['phases'],
										'parent' : cymsectiondevice[load]['parent'],
										'nominal_votlage' : str(feeder_VLN),
										'load_class' : 'C'}
				for phase in loads[load]['phases']:
					if phase not in ['N','D']:
						loads[load]['constant_power_{:s}'.format(phase)] = cymcustomerload[load]['constant_power_{:s}'.format(phase)]
			elif load not in tpns.keys():
				if cymsectiondevice[load]['name'] not in loadNames:
					loadNames.append(cymsectiondevice[load]['name'])
					# for phase in cymsectiondevice[load]['phases']: #jfk.  was looking for phases that don't correspond to loads
					for phase in cymcustomerload[load]['phases']: #jfk
						if phase not in ['N', 'D']:
							try:
								spctRating = _find_SPCT_rating(str(cymcustomerload[load]['constant_power_{:s}'.format(phase)]))
							except:
								spctRating = _find_SPCT_rating(str(cymcustomerload[load]['constant_power_A']))
								cymcustomerload[load]['constant_power_{:s}'.format(phase)] = cymcustomerload[load]['constant_power_A']
							spct_cfgs['SPCTconfig{:s}{:s}'.format(load, phase)] = { 'object' : 'transformer_configuration',
								'name' : 'SPCTconfig{:s}{:s}'.format(load, phase),
								'connect_type' : 'SINGLE_PHASE_CENTER_TAPPED',
								'install_type' : 'POLETOP',
								'primary_voltage' : str(feeder_VLN),
								'secondary_voltage' : '120',
								'power_rating' : spctRating,
								'power{:s}_rating'.format(phase) : spctRating,
								'impedance' : '0.00033+0.0022j'}
							spcts['SPCT{:s}{:s}'.format(load, phase)] = { 'object' : 'transformer',
								'name' : 'SPCT{:s}{:s}'.format(load, phase),
								'phases' : '{:s}S'.format(phase),
								'from' : cymsectiondevice[load]['parent'],
								'to' : 'tpm{:s}{:s}'.format(load, phase),
								'configuration' : 'SPCTconfig{:s}{:s}'.format(load, phase)}
							tpms['tpm{:s}{:s}'.format(load, phase)] = {'object' : 'triplex_meter',
								'name' : 'tpm{:s}{:s}'.format(load, phase),
								'phases' : '{:s}S'.format(phase),
								'nominal_voltage' : '120',
								'latitude' : str(float(nodes[cymsectiondevice[load]['parent']]['latitude']) + random.uniform(-5, 5)),
								'longitude' : str(float(nodes[cymsectiondevice[load]['parent']]['longitude']) + random.uniform(-5, 5))}
							tpns['tpn{:s}{:s}'.format(load, phase)] = {'object' : 'triplex_node',
								'name' : 'tpn{:s}{:s}'.format(load, phase),
								'phases' : '{:s}S'.format(phase),
								'nominal_voltage' : '120',
								'parent' : 'tpm{:s}{:s}'.format(load, phase),
								'power_12' : cymcustomerload[load]['constant_power_{:s}'.format(phase)],
								'latitude' : str(float(tpms['tpm{:s}{:s}'.format(load, phase)]['latitude']) + random.uniform(-5, 5)),
								'longitude' : str(float(tpms['tpm{:s}{:s}'.format(load, phase)]['longitude']) + random.uniform(-5, 5))}
	#jfk.  I can't find the band_center anywhere in the cyme databaes files.
	#Unfortunately, the only way to deal with this is by looking at the cyme user interfrace.
	# Create regulator and regulator configuration dictionaries
	#Now, I just have the values hardcoded in.  For example...
	regulator_bandcenters = {'REG_BOYD_000_105581299': 126, #newlinville
							'REG_HIGHLAND_000_105563434': 126,
							'REG_PARKESBURG_001_105599479': 126,
							'REG_PARKESBURG_002_105581381': 126,
							'REG_2449_36H5B19983': 124,
							'REG_7305_45D3A4_0806': 124,
							'REG_7526_45D3C3': 124,
							'REG_40701_52B3F3': 124,
							'REG_STOTTSVILLE_000_105581307': 125,
							'6': 126, #chestnust
							'BOOT_JACK_000_105622980': 125, #bootjack
							'REG_BOOT_JACK_000_105622980': 125,
							'REG_4631_52D4C7': 124,
							'REG_4955_52C4H83614': 124,
							'REG_41221_52D4C7': 124,
							'REG_49925_52D4C8': 124,
							'REG_60926_52E3A8': 124}

	reg_cfgs = {}
	regs = {}
	for reg in cymsectiondevice.keys():
		if cymsectiondevice[reg]['device_type'] == 4:
			if reg not in cymregulator.keys():
				print "There is no regulator spec for ", reg, " in the network database provided.\n"
			else:
				regEq = cymregulator[reg]['equipment_name']
				if regEq not in cymeqregulator.keys():
					raiseTaps = '16'
					lowerTaps = '16'
				else:
					raiseTaps = cymeqregulator[regEq]['raise_taps']
					lowerTaps = cymeqregulator[regEq]['lower_taps']
				reg_nominalvoltage = float(cymeqregulator[regEq]['nominal_voltage'])*1000.0
				#HACK: bandwidth sometimes set to none.
				if not cymeqregulator[regEq]['bandwidth']:
					#HACK: just choose 10% of nominal. Good idea? TBD.
					safeRegBand = 0.10 * reg_nominalvoltage
				else:
					safeRegBand = float(cymeqregulator[regEq]['bandwidth'])
				reg_bandwidth = str(safeRegBand*reg_nominalvoltage/120.0)
				#jfk. Need to have separate regulator configurations for each regulator
				# Cyme holds tap position in regulator, but Gridlabd holds tap position in configuration
				regEq = regEq +'_' + reg
				if reg in regulator_bandcenters.keys():
					band_center120 = regulator_bandcenters[reg]
				else:
					warnings.warn('Bandcenter info not provided. Setting bandcenter to 1.05.')
					band_center120 = 126.0
				warnings.warn('Regulators hardcoded to OUTPUT_VOLTAGE.')
				ph = cymsectiondevice[reg]['phases'].replace('N', '')
				if regEq not in reg_cfgs.keys():
					reg_cfgs[regEq] = {'object' : 'regulator_configuration',
						'name' : regEq, #jfk
						'connect_type' : 'WYE_WYE',
						'band_center' : str(float(reg_nominalvoltage)*(band_center120/120.0)),
						'band_width' : reg_bandwidth,
						'regulation' : str(cymregulator[reg]['regulation']),
						'time_delay' : '30.0',
						'dwell_time' : '5',
						'Control' : 'OUTPUT_VOLTAGE', #'MANUAL' #
						'control_level' : 'INDIVIDUAL',
						'raise_taps' : raiseTaps,
						'lower_taps' : lowerTaps}
					for phase in ph:
						reg_cfgs[regEq]['tap_pos_{:s}'.format(phase)] = str(cymregulator[reg]['tap_pos_{:s}'.format(phase)])
				if reg not in reg_cfgs.keys():
					regs[reg] = {'object' : 'regulator',
										'name' : reg,
										'phases' : ph,
										'from' : cymsectiondevice[reg]['from'],
										'to' : cymsectiondevice[reg]['to'],
										'configuration' : regEq} #jfk

	# Create photovoltaic, inverter, and meter dictionaries
	pv_sec = {}
	for pv in cymsectiondevice.keys():
		if cymsectiondevice[pv]['device_type'] == 45:
			if pv not in cymphotovoltaic.keys():
				print "There is no PV spec for ", pv, " in the network database provided.\n"
			else:
				pv_sec[pv+'meter']={'object':'meter',
									'name': pv+'meter',
									'parent':cymsectiondevice[pv]['parent'],
									'latitude':cymsectiondevice[pv]['toLatitude'],
									'longitude':cymsectiondevice[pv]['toLongitude']}
				pv_sec[pv+'inv'] = {'object':'inverter',
									'name': 'n'+pv+'inv',
									'parent': pv+'meter',
									'latitude':cymsectiondevice[pv]['toLatitude'],
									'longitude':cymsectiondevice[pv]['toLongitude']}
				pv_sec[pv] = {'object' : 'solar',
							'name' : pv,
							'efficiency': cymeqphotovoltaic[cymphotovoltaic[pv]['configuration']]['efficiency'],
							'area': 1000 * 0.075 * float(cymeqphotovoltaic[cymphotovoltaic[pv]['configuration']]['voltage']) * float(cymeqphotovoltaic[cymphotovoltaic[pv]['configuration']]['current']),
							'parent': pv+'inv',
							'latitude':cymsectiondevice[pv]['toLatitude'],
							'longitude':cymsectiondevice[pv]['toLongitude']}
	# Create battery dictionaries
	bat_sec = {}
	for bat in cymsectiondevice.keys():
		if cymsectiondevice[bat]['device_type'] == 80:
			if bat not in cymbattery.keys():
				print "There is no battery spec for ", bat, " in the network database provided.\n"
			else:
				bat_sec[cymsectiondevice[bat]['section_name']] = {'object':'meter',
									'name': cymsectiondevice[bat]['section_name'],
									'parent':cymsectiondevice[bat]['parent']
									}
				bat_sec[bat+'inv'] = {'object':'inverter',
									'name':'n'+bat+'inv',
									'generator_mode':'CONSTANT_PQ',
									'parent':cymsectiondevice[bat]['section_name'],
									'phases':'BS',
									'four_quadrant_control_mode': 'LOAD_FOLLOWING',
									'generator_status': 'ONLINE',
									'inverter_type': 'FOUR_QUADRANT',
									'discharge_off_threshold': 7454,
									'rated_power':cymeqbattery[cymbattery[bat]['configuration']]['rated_storage_energy'],
									'charge_off_threshold': 6148,
									'max_charge_rate':cymeqbattery[cymbattery[bat]['configuration']]['max_charging_power'],
									'max_discharge_rate': cymeqbattery[cymbattery[bat]['configuration']]['max_discharging_power'],
									'discharge_lockout_time': 60,
									'charge_lockout_time': 60,
									'inverter_efficiency': cymeqbattery[cymbattery[bat]['configuration']]['round_trip_efficiency']}
				bat_sec[bat] = {'object':'battery',
								'name': bat,
								'state_of_charge':1.0,
								'parent': bat+'inv',
								'latitude':cymsectiondevice[bat]['toLatitude'],
								'longitude':cymsectiondevice[bat]['toLongitude'],
								'round_trip_efficiency': cymeqbattery[cymbattery[bat]['configuration']]['round_trip_efficiency'],
								'generator_mode':'SUPPLY_DRIVEN',
								'generator_status':'ONLINE',
								'battery_state':1.0,
								'battery_capacity':cymeqbattery[cymbattery[bat]['configuration']]['rated_storage_energy'],
								'battery_type':'LI_ION',
								'use_internal_battery_model':'TRUE'}
	# Create generator dictionaries
	gen_secs = {}
	for gen in cymsectiondevice.keys():
		if cymsectiondevice[gen]['device_type'] == 37:
			if gen not in cymgenerator.keys():
				print "There is no generator spec for ", gen, " in the network database provided.\n"
			else:
				gen_secs[gen] = {'object':'diesel_dg',
								'name':gen,
								'parent': cymsectiondevice[gen]['parent'],
								'Gen_type':2,
								'Gen_mode':1,
								'TotalRealPow':cymgenerator[gen]['generation'],
								'pf': cymgenerator[gen]['power_factor']}
	# Create transformer and transformer configuration dictionaries
	xfmr_cfgs = {}
	xfmrs = {}
	for xfmr in cymsectiondevice.keys():
		if cymsectiondevice[xfmr]['device_type'] == 47:
			if xfmr not in cymxfmr.keys():
				print "There is no xmfr spec for ", xfmr, " in the network database provided.\n"
			else:
				xfmrEq = cymxfmr[xfmr]['equipment_name']
				if xfmrEq == xfmr:
					suffix = 'cfg'
				else:
					suffix = ''
				ph = cymsectiondevice[xfmr]['phases'].replace('N', '')
				phNum = 0
				if 'A' in ph:
					phNum += 1.0
				if 'B' in ph:
					phNum += 1.0
				if 'C' in ph:
					phNum += 1.0
				if xfmrEq not in cymeqautoxfmr.keys():
					print "There is no xmfr spec for ", xfmrEq, " in the network database provided.\n"
				else:
					if xfmrEq not in xfmr_cfgs.keys():
						xfmr_cfgs[xfmrEq] = {'object' : 'transformer_configuration',
															'name' : xfmrEq + suffix,
															'connect_type' : 'WYE_WYE',
															'primary_voltage' : '{:0.6f}'.format(cymeqautoxfmr[xfmrEq]['PrimaryVoltage']*math.sqrt(3)), #jfk
															'secondary_voltage' : '{:0.6f}'.format(cymeqautoxfmr[xfmrEq]['SecondaryVoltage']*math.sqrt(3)), #jfk
															'impedance' : cymeqautoxfmr[xfmrEq]['impedance'],
															'power_rating' : '{:0.0f}'.format(cymeqautoxfmr[xfmrEq]['PrimaryRatedCapacity'])}
						for phase in ph:
							if phase not in ['N', 'D']:
								xfmr_cfgs[xfmrEq]['power{:s}_rating'.format(phase)] = '{:0.6f}'.format(cymeqautoxfmr[xfmrEq]['PrimaryRatedCapacity']/phNum)
				if xfmr not in xfmrs.keys():
					xfmrs[xfmr] = {'object' : 'transformer',
											'name' : xfmr,
											'phases' : ph,
											'from' : cymsectiondevice[xfmr]['from'],
											'to' : cymsectiondevice[xfmr]['to'],
											'configuration' : xfmrEq + suffix}
		#jfk.  this block is nearly identical to the above.
		elif cymsectiondevice[xfmr]['device_type'] == 5:
			if xfmr not in cymxfmr.keys():
				print "There is no xmfr spec for ", xfmr, " in the network database provided.\n"
			else:
				xfmrEq = cymxfmr[xfmr]['equipment_name']
				if xfmrEq == xfmr:
					suffix = 'cfg'
				else:
					suffix = ''
				ph = cymsectiondevice[xfmr]['phases'].replace('N', '')
				phNum = 0
				if 'A' in ph:
					phNum += 1.0
				if 'B' in ph:
					phNum += 1.0
				if 'C' in ph:
					phNum += 1.0
				if xfmrEq not in cymeqxfmr.keys():
					print "There is no xmfr spec for ", xfmrEq, " in the network database provided.\n"
				else:
					if xfmrEq not in xfmr_cfgs.keys():
						xfmr_cfgs[xfmrEq] = {'object' : 'transformer_configuration',
															'name' : xfmrEq + suffix,
															'connect_type' : 'WYE_WYE',
															'primary_voltage' : '{:0.6f}'.format(cymeqxfmr[xfmrEq]['PrimaryVoltage']*math.sqrt(3)), #jfk
															'secondary_voltage' : '{:0.6f}'.format(cymeqxfmr[xfmrEq]['SecondaryVoltage']*math.sqrt(3)), #jfk
															# 'resistance': '0.000000001',
											 				# 'reactance': '0.0000000006',
															'impedance' : cymeqxfmr[xfmrEq]['impedance'],
															'power_rating' : '{:0.0f}'.format(cymeqxfmr[xfmrEq]['PrimaryRatedCapacity'])}
						for phase in ph:
							if phase not in ['N', 'D']:
								xfmr_cfgs[xfmrEq]['power{:s}_rating'.format(phase)] = '{:0.6f}'.format(cymeqxfmr[xfmrEq]['PrimaryRatedCapacity']/phNum)
				if xfmr not in xfmrs.keys():
					xfmrs[xfmr] = {'object' : 'transformer',
											'name' : xfmr,
											'phases' : ph,
											'from' : cymsectiondevice[xfmr]['from'],
											'to' : cymsectiondevice[xfmr]['to'],
											'configuration' : xfmrEq + suffix}
		elif cymsectiondevice[xfmr]['device_type'] == 48:
			if xfmr not in cym3wxfmr.keys():
				print "There is no xfmr spec for ", xfmr, " in the network database provided.\n"
			else:
				xfmrEq = cym3wxfmr[xfmr]['equipment_name']
				if xfmrEq == xfmr:
					suffix = 'cfg'
				else:
					suffix = ''
				ph = cymsectiondevice[xfmr]['phases'].replace('N', '')
				phNum = 0
				if 'A' in ph:
					phNum += 1.0
				if 'B' in ph:
					phNum += 1.0
				if 'C' in ph:
					phNum += 1.0
				if xfmrEq not in cymeq3wautoxfmr.keys():
					print "There is no xfmr spec for ", xfmrEq, " in the network database provided.\n"                    
				else:
					if xfmrEq not in xfmr_cfgs.keys():
						xfmr_cfgs[xfmrEq] = {'object' : 'transformer_configuration',
															'name' : xfmrEq + suffix,
															'connect_type' : 'WYE_WYE',
															'primary_voltage' : '{:0.6f}'.format(cymeq3wautoxfmr[xfmrEq]['PrimaryVoltage']),
															'secondary_voltage' : '{:0.6f}'.format(cymeq3wautoxfmr[xfmrEq]['SecondaryVoltage']),
															'impedance' : cymeq3wautoxfmr[xfmrEq]['impedance'],
															'power_rating' : '{:0.0f}'.format(cymeq3wautoxfmr[xfmrEq]['PrimaryRatedCapacity'])}
						for phase in ph:
							if phase not in ['N', 'D']:
								xfmr_cfgs[xfmrEq]['power{:s}_rating'.format(phase)] = '{:0.6f}'.format(cymeq3wautoxfmr[xfmrEq]['PrimaryRatedCapacity']/phNum)
				if xfmr not in xfmrs.keys():
					xfmrs[xfmr] = {'object' : 'transformer',
											'name' : xfmr,
											'phases' : ph,
											'from' : cymsectiondevice[xfmr]['from'],
											'to' : cymsectiondevice[xfmr]['to'],
											'configuration' : xfmrEq + suffix}
	#Add dictionaries to feeder tree object
	#jfk.  giving an hour for everything to settle down.  needed for regulators and verification
	genericHeaders = [    {"timezone":"PST+8PDT","stoptime":"'2000-01-01 01:00:00'","starttime":"'2000-01-01 00:00:00'","clock":"clock"},
						{"omftype":"#set","argument":"minimum_timestep=60"},
						{"omftype":"#set","argument":"profiler=1"},
						{"omftype":"#set","argument":"relax_naming_rules=1"},
						{"omftype":"module","argument":"generators"},
						{"omftype":"module","argument":"tape"},
						{"module":"residential","implicit_enduses":"NONE"},
						{"solver_method":"NR","NR_iteration_limit":"50","module":"powerflow"}]
	for headId in xrange(len(genericHeaders)):
		glmTree[headId] = genericHeaders[headId]
	key = len(glmTree)
	objectList = [ohl_conds, ugl_conds, ohl_spcs, ohl_configs , ugl_sps, ohl_cfgs, ugl_cfgs, xfmr_cfgs, spct_cfgs, reg_cfgs, meters, nodes, loads, tpms, tpns, ohls, ugls, xfmrs, spcts, regs, swObjs, rcls, sxnlrs, fuses, caps, bat_sec, pv_sec, gen_secs, reactors]
	for objDict in objectList:
		if len(objDict) > 0:
			for obj in objDict.keys():
				glmTree[key] = copy.deepcopy(objDict[obj])
				key = len(glmTree)
	# Find and fix duplicate names between nodes and links
	for x in glmTree.keys():
		if 'object' in glmTree[x].keys() and glmTree[x]['object'] in ['node', 'meter', 'triplex_meter', 'triplex_node']:
			glmTree[x]['name'] = 'n' +  glmTree[x]['name']
		if 'from' in glmTree[x].keys():
			glmTree[x]['from'] = 'n' +  glmTree[x]['from']
			glmTree[x]['to'] = 'n' +  glmTree[x]['to']
		if 'parent' in glmTree[x].keys():
			glmTree[x]['parent'] = 'n' +  glmTree[x]['parent']
	# FINISHED CONVERSION FROM THE DATABASES****************************************************************************************************************************************************   
	for key in glmTree.keys():
		# if ('from' in glmTree[key].keys() and 'to' not in glmTree[key].keys()) or ('to' in glmTree[key].keys() and 'from' not in glmTree[key].keys()):
		if 'object' in glmTree[key].keys() and glmTree[key]['object'] in ['overhead_line','underground_line','regulator','transformer','switch','fuse', 'series_reactor'] and ('to' not in glmTree[key].keys() or 'from' not in glmTree[key].keys()):
			#print ('Deleting malformed link')
			#print [glmTree[key]['name'], glmTree[key]['object']]
			del glmTree[key]
	# Create list of all from and to node names
	LinkedNodes = {}
	toNodes = []
	fromNodes = []
	for key in glmTree.keys():
		#jfk.  dont want phase information to be passed on by open switches
		#I have scenarios like:  phaseC -/ - phaseB
		if glmTree[key].get('object','') == 'switch':
			if 'OPEN' in glmTree[key].values():
				continue


		if 'to' in glmTree[key].keys():
			ph = LinkedNodes.get(glmTree[key]['from'], '')
			LinkedNodes[glmTree[key]['from']] = ph + glmTree[key]['phases']
			ph = LinkedNodes.get(glmTree[key]['to'], '')
			LinkedNodes[glmTree[key]['to']] = ph + glmTree[key]['phases']
			if glmTree[key]['to'] not in toNodes:
				toNodes.append(glmTree[key]['to'])
			if glmTree[key]['from'] not in fromNodes:
				fromNodes.append(glmTree[key]['from'])
	for node in fromNodes:
		if node not in toNodes and node != 'n' + swingBus:
			print(node)
	# Find the unique phase information and place them in the node like object dictionaries
	for node in LinkedNodes.keys():
		phase = ''
		ABCphases = 0
		if 'A' in LinkedNodes[node]:
			phase = phase + 'A'
			ABCphases = ABCphases + 1
		if 'B' in LinkedNodes[node]:
			phase = phase + 'B'
			ABCphases = ABCphases + 1
		if 'C' in LinkedNodes[node]:
			phase = phase + 'C'
			ABCphases = ABCphases + 1
		if 'S' in LinkedNodes[node] and ABCphases == 1 and node not in fromNodes:
			phase = phase + 'S'
		else:
			phase = phase + 'N'
			
		for x in glmTree.keys():
			if 'name' in glmTree[x].keys() and glmTree[x]['name'] == node:
				glmTree[x]['phases'] = phase
	
	# Take care of open switches
	swFromNodes = {}
	swToNodes = {}
	for x in glmTree.keys():
		if 'from' in glmTree[x].keys():
			if glmTree[x]['from'] not in swFromNodes.keys():
				swFromNodes[glmTree[x]['from']] = 1
			else:
				swFromNodes[glmTree[x]['from']] += 1
			if glmTree[x]['to'] not in swToNodes.keys():
				swToNodes[glmTree[x]['to']] = 1
			else:
				swToNodes[glmTree[x]['to']] += 1
	deleteKeys = []
	for x in glmTree.keys():
		if glmTree[x].get('phase_A_state', '') == 'OPEN' or glmTree[x].get('phase_B_state', '') == 'OPEN' or glmTree[x].get('phase_C_state', '') == 'OPEN':
			if swToNodes[glmTree[x]['to']] > 1:
				deleteKeys.append(x)
			elif swFromNodes.get(glmTree[x]['to'], 0) > 0:
				for phase in glmTree[x]['phases']:
					if phase not in ['N', 'D']:
						glmTree[x]['phase_{:s}_state'.format(phase)] = 'CLOSED'
			else:
				deleteKeys.append(x)
				for y in glmTree.keys():
					if glmTree[y].get('name', '') == glmTree[x]['to']:#jfk was glmTree[y].get['name', '']  #typo with the brackets
						deleteKeys.append(y)
	for key in deleteKeys:
		del glmTree[key]
		

	def _fixNominalVoltage(glm_dict, volt_dict):
		for x in glm_dict.keys():
			if 'from' in glm_dict[x].keys() and glm_dict[x]['from'] in volt_dict.keys() and glm_dict[x]['to'] not in volt_dict.keys(): 
				if glm_dict[x]['object'] == 'transformer':
					# get secondary voltage from transformer configuration
					if'SPCT' in glm_dict[x]['name']:
						nv = '120.0'
					else:
						cnfg = glm_dict[x]['configuration']
						for y in glm_dict.keys():
							if 'name' in glm_dict[y].keys() and glm_dict[y]['name'] == cnfg:
								nv = glm_dict[y]['secondary_voltage']
					volt_dict[glm_dict[x]['to']] = nv
				elif glm_dict[x]['object'] == 'regulator':
					volt_dict[glm_dict[x]['to']] = volt_dict[glm_dict[x]['from']]                 
					cnfg = glm_dict[x]['configuration']
					nv = volt_dict[glm_dict[x]['from']]  
					for y in glm_dict.keys():
						if glm_dict[y].get('name', '') == cnfg:
							pass
							# glmTree[y]['band_center'] = nv
							# glmTree[y]['band_width'] = str(float(glmTree[y]['band_width'])*float(glmTree[y]['band_center']))
				else:              
					volt_dict[glm_dict[x]['to']] = volt_dict[glm_dict[x]['from']]
			elif 'parent' in glm_dict[x].keys() and glm_dict[x]['parent'] in volt_dict.keys() and glm_dict[x]['name'] not in volt_dict.keys():
				volt_dict[glm_dict[x]['name']] = volt_dict[glm_dict[x]['parent']]
				
	parent_voltage = {}
	current_parents = len(parent_voltage)
	previous_parents = 0
	
	for obj in glmTree:
		if 'bustype' in glmTree[obj] and glmTree[obj]['bustype'] == 'SWING':
			parent_voltage[glmTree[obj]['name']] = glmTree[obj]['nominal_voltage']
			current_parents = len(parent_voltage)
			
	while current_parents > previous_parents:
		_fixNominalVoltage(glmTree, parent_voltage)
		previous_parents = current_parents
		current_parents = len(parent_voltage)
		
	for x in glmTree.keys():
		if glmTree[x].get('name', '') in parent_voltage.keys():
			glmTree[x]['nominal_voltage'] = parent_voltage[glmTree[x].get('name', '')]
	# Delete nominal_voltage from link objects
	del_nom_volt_list = ['overhead_line', 'underground_line', 'regulator', 'transformer', 'switch', 'fuse', 'ZIPload', 'diesel_dg', 'solar','inverter']
	for x in glmTree:
		if 'object' in glmTree[x].keys() and glmTree[x]['object'] in del_nom_volt_list and 'nominal_voltage' in glmTree[x].keys():
			del glmTree[x]['nominal_voltage']
	
	# Delete neutrals from links with no neutrals
	for x in glmTree.keys():
		if 'object' in glmTree[x].keys() and glmTree[x]['object'] in ['underground_line', 'regulator', 'transformer', 'switch', 'fuse', 'capacitor', 'series_reactor']:
			glmTree[x]['phases'] = glmTree[x]['phases'].replace('N', '')
		elif 'object' in glmTree[x].keys() and glmTree[x]['object'] == 'overhead_line':
			if glmTree[x]['configuration'] not in ohl_neutral:
				glmTree[x]['phases'] = glmTree[x]['phases'].replace('N', '')
		if 'object' in glmTree[x].keys() and glmTree[x]['object'] in ['node', 'meter']:
			try:
				glmTree[x]['phases'] = glmTree[x]['phases'].replace('S', '')
				if 'N' not in glmTree[x]['phases']:
					glmTree[x]['phases'] = glmTree[x]['phases'] + 'N'
			except:
				pass
	#TODO: have this missing nodes report not put files all over the place.
	# checkMissingNodes(nodes, cymsectiondevice, objectList, feeder_id, modelDir, cymsection)
	#jfk.  add regulator to source
	biggestkey = max(glmTree.keys())
	glmTree[biggestkey+1] = {
		'object': 'node',
		'name': 'sourcenode',
		'phases': 'ABC',
		'nominal_voltage': cymsource[_fixName(swingBus)]['nominal_voltage'],
		'bustype': 'SWING'
	}
	glmTree[biggestkey+2] = {
		'object': 'regulator',
		'name': 'sourceregulator',
		'phases': 'ABC',
		'from': 'sourcenode',
		'to': 'n' + swingBus,
		'configuration': 'ss_regconfiguration'
	}
	glmTree[biggestkey+3] = {
		'object': 'regulator_configuration',
		'name': 'ss_regconfiguration',
		'band_center': cymsource[_fixName(swingBus)]['nominal_voltage'], #HACK: source_voltage set to nominal.
		'Control': 'OUTPUT_VOLTAGE',
		'connect_type': 'WYE_WYE',
		'raise_taps': '50', #want to be very close to desired voltage for agreement with cyme
		'lower_taps': '50',
		'band_width': '2.0', #bandwidth should be very small for all voltage levels
		'regulation': '0.1',
		'dwell_time': '5',
		'tap_pos_A': '0',
		'tap_pos_B': '0',
		'tap_pos_C': '0',
		'time_delay': '30.0',
		'control_level': 'INDIVIDUAL'
	}
	# Clean up the csvDump.
	shutil.rmtree(pJoin(modelDir,'cymeCsvDump'))
	return glmTree

def _tests(keepFiles=True):
	testFile = ['IEEE13.mdb']
	inputDir = './static/testFiles/'
	# outputDir = tempfile.mkdtemp()
	outputDir = './scratch/cymeToGridlabTests/'
	exceptionCount = 0
	try:
		shutil.rmtree(outputDir)
	except:
		pass # no test directory yet.
	finally:
		os.mkdir(outputDir)
	locale.setlocale(locale.LC_ALL, 'en_US')
	for db_network in testFile:
		try:
			# Main conversion of CYME model.
			cyme_base = convertCymeModel(inputDir + db_network, inputDir)    
			glmString = feeder.sortedWrite(cyme_base)
			testFilename = db_network[:-4]
			gfile = open(inputDir+testFilename+".glm", 'w')
			gfile.write(glmString)
			gfile.close()
			inFileStats = os.stat(pJoin(inputDir,db_network))
			outFileStats = os.stat(pJoin(inputDir,testFilename+".glm"))
			inFileSize = inFileStats.st_size
			outFileSize = outFileStats.st_size
			treeObj = feeder.parse(inputDir+testFilename+".glm")
			print 'WROTE GLM FOR ' + db_network
			with open(pJoin(outputDir,'convResults.txt'),'a') as resultsFile:
				resultsFile.write('WROTE GLM FOR ' + testFilename + "\n")
				resultsFile.write('Input .mdb File Size: ' + str(locale.format("%d", inFileSize, grouping=True))+'\n')
				resultsFile.write('Output .glm File Size: '+ str(locale.format("%d", outFileSize, grouping=True))+'\n')
		except:
			print 'FAILED CONVERTING'
			testFilename = 'failed'
			with open(pJoin(outputDir,'convResults.txt'),'a') as resultsFile:
				resultsFile.write('FAILED CONVERTING ' + testFilename + "\n")
			traceback.print_exc()
			exceptionCount += 3
			continue # No use trying to draw or run if conversion fails.
		try:
			# Draw the GLM.
			myGraph = feeder.treeToNxGraph(cyme_base)
			feeder.latLonNxGraph(myGraph, neatoLayout=False)
			plt.savefig(outputDir + testFilename+".png")
			with open(pJoin(outputDir,'convResults.txt'),'a') as resultsFile:
				resultsFile.write('DREW GLM FOR ' + testFilename + "\n")
			print 'DREW GLM OF ' + db_network
		except:
			exceptionCount += 1
			with open(pJoin(outputDir,'convResults.txt'),'a') as resultsFile:
				resultsFile.write('FAILED DRAWING' + testFilename + "\n")
			print 'FAILED DRAWING ' + db_network
		try:
			# Run powerflow on the GLM.
			output = gridlabd.runInFilesystem(treeObj, keepFiles=True, workDir=outputDir)
			if output['stderr'] == "":
				gridlabdStderr = "GridLabD ran successfully without error."
			else:
				gridlabdStderr =  output['stderr']
			with open(outputDir + testFilename +".JSON",'w') as outFile:
				json.dump(output, outFile, indent=4)
			with open(pJoin(outputDir,'convResults.txt'),'a') as resultsFile:
				resultsFile.write('RAN GRIDLAB ON ' + testFilename + "\n")
				resultsFile.write('STDERR: ' + gridlabdStderr + "\n\n")
			print 'RAN GRIDLAB ON ' + db_network
		except:
			exceptionCount += 1
			with open(pJoin(outputDir,'convResults.txt'),'a') as resultsFile:
				resultsFile.write('POWERFLOW FAILED FOR ' + testFilename + "\n")
			print 'POWERFLOW FAILED'
	if not keepFiles:
		shutil.rmtree(outputDir)
	return exceptionCount    

if __name__ == '__main__':
	_tests()

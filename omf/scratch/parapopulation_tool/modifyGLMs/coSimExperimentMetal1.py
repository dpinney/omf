"""
This script describes a co-simulation of a transmission and distribution power system model. The simulation
uses MATPOWER and GridLAB-D

Code dependencies:
   	coSimConfiguration.py
   	parseGLM.py
   	feederConfiguration.py
   	feegerGenerator.py
	loads.py
   	tape.py
   	externalControl.py
   	modelDependency (GridLAB-D, MATPWOER related files)
   	MATPOWER 5.1 or later (http://www.pserc.cornell.edu/matpower/)
   	Pre-compiled MATPOWER matlab libraries (see additional MATLAB script to compile these)
	Python (2.7) packages:
		numpy (http://www.numpy.org/)
		scipy (https://www.scipy.org/)
		tqdm (https://pypi.python.org/pypi/tqdm)
		subprocess (https://docs.python.org/2/library/subprocess.html)
		os (https://docs.python.org/2/library/os.html)
		random (https://docs.python.org/2/library/random.html)
		math (https://docs.python.org/2/library/math.html)
		copy (https://docs.python.org/2/library/copy.html)
		__future__ (https://docs.python.org/2/library/__future__.html)
		re (https://docs.python.org/2/library/re.html)
		warnings (https://docs.python.org/2/library/warnings.html)
		time (https://docs.python.org/2/library/time.html)
		shutil (https://docs.python.org/2/library/shutil.html)
		multiprocessing (https://docs.python.org/2/library/multiprocessing.html)
		datetime (https://docs.python.org/2/library/datetime.html)

Software dependencies:
	GridLAB-D 4.0 RC-1 (https://github.com/gridlab-d)
	FNCS 2 (https://github.com/FNCS/fncs)
	MATPOWER 5.1 or later (http://www.pserc.cornell.edu/matpower/)
	MATLAB R2015b (or MCR) or later (http://www.mathworks.com or https://www.mathworks.com/products/compiler/mcr.html)

Guide for using scripts
	This script is the master script and it will create a contained experiment with the settings specified in
	the beginning of this script

	If this is the first time running you need to compile the MATLAB libraries for the MATPOWER wrapper. A
	MATLAB script called "compileMATPOWERLibraries.m"  is provided in modelDependency -> matpower to do so.

	Settigs for the script is divided into to sections
		Co-simulation configuration
			These setting are specified in the beginning of this script

		Feeder configuration
      		All changes to what is implemented is located "feederConfiguration.py". In this you can add more
      		known GLM system (for now "4BusSystem" and prototypical feeders are avaialble) along with specific
      		settings for each system. In this file you can specify what technologies to deploy and change basic
      		behaviors of the technologies.

	 		When implementing houses the original GLM needs to be of a certain structure. In order to deploy
	 		residential houses you need to specify the secondary side of the feeder i.e. you have to have
	 		triplex_node objects specified with either constant power1 or power12 specified. Special case for
	 		triplec_node is where you specify the exact number of house to implement by setting number_of_houses.

	Procedure to create experiemnt
    	1) Place this file with the rest of the dependent file wherever you choose on your computer. I suggest
    	   to keep it in the already defined folder structure

		2) update the file paths and settings below along with feeder configurations

		3) execute this script on the machine you want to run the experiment on and let it work its magic

	Procedure to run the experiment
		1) navigate to the experiment you created. It will be in the experiments folder

		2) your experiment will include three convenience scripts that will help execute the experiment. The
		   copyAll.sh script will copy all the required MATPOWER dependencies to the right folders. This script
		   is already run acutmatically so no need to do anything. The killAll.sh script will end any previously
		   executed experiemnts and ensure that you don't run into any issues. runAll.sh will execute the actual
		   experiment. It is always recommend to run killAll followed by runAll. If succesfull no output will be
		   present in the terminal. Each application is executed in a seperate shell and the output is redirected
		   to simLog.out files

		3) progress on the experiment can be found in the simLog.out files. A seperate file for each simulator is
		   present. The log file for FNCS itself will be located at the root of the experiment folder

Imporvements to come in the future:
	Upload to public repository so everyone can use these scripts


Created March 28, 2017 by Jacob Hansen (jacob.hansen@pnnl.gov)

Copyright (c) 2017 Battelle Memorial Institute.  The Government retains a paid-up nonexclusive, irrevocable
worldwide license to reproduce, prepare derivative works, perform publicly and display publicly by or for the
Government, including the right to distribute to other Government contractors.
"""

from __future__ import division
import sys, os
import parseGLM
import coSimConfiguration
import feederConfiguration
import time, math, os, shutil, multiprocessing, tqdm, datetime
import json as js

if __name__ == '__main__':
	inputdatafile = file(str(sys.argv[1]))
	input_data_dict = js.load(inputdatafile)

	main(input_data_dict)
	# ---------------------------------------------------------------
	# ----------------------- Settings ------------------------------
	# ---------------------------------------------------------------
# NRECA EDIT: Main function added so it can be called later
def main(input_data_dict):
	start = time.time()
	
	
	
	date_list = []
	date_list.append(input_data_dict["startdate"])
	date_list.append(input_data_dict["enddate"])
	date_list.append(input_data_dict["recordstart"])
	date_list.append(input_data_dict["recordend"])
	
	
	'''
	date_list.append(str(sys.argv[3])+ ' ' + str(sys.argv[4]))
	date_list.append(str(sys.argv[5])+ ' ' + str(sys.argv[6]))
	date_list.append(str(sys.argv[7])+ ' ' + str(sys.argv[8]))
	date_list.append(str(sys.argv[9])+ ' ' + str(sys.argv[10]))
	'''

	
	#print (date_list)
	# name of the experiment
	experimentName = input_data_dict["testfolder"]  #str(sys.argv[2]) #'tester_1'

	# number of distribution systems in the experiment
	distributionNumber = input_data_dict["numoffeeders"]  #int(sys.argv[1])   #10

	# software paths on the machine you use
	fncsExecutablePath = '/home/ccsiDemo/fncsInstall'
	gridlabdExecutablePath = '/home/ccsiDemo/gldInstall'
	matlabExecutablePath = '/usr/local/MATLAB/v90'
	zeroMQLibraryPath = '/home/ccsiDemo/zeroMQInstall'
	CZMQLibraryPath = '/home/ccsiDemo/CZMQInstall'

	# this assumes that everything associated with this experiment is in a certain folder structure. This is the path to the root folder
	rootPath = input_data_dict["rootpath"] #'/home/huan495/parapopulation_tool'
	# rootPath = '/home/ccsiDemo/FY17_DEMO_1'

	# relative file path that contains the GLMs to extract
	feederFilePath = '/modelDependency/feeders/taxonomy'
	#feederFilePath = '/modelDependency/feeders'

	# relative file path that contains include files for the experiment
	includeFilePath = '/modelDependency'

	# relative path to where you want the experiment outputs
	# NRECA EDIT experimentFilePath now pulled from json dictionary input
	experimentFilePath = input_data_dict['experimentFilePath']

	# relative path to MATPOWER wrapper related files
	matpowerFilePath = '/modelDependency/matpower'

	# relative path to aggregator related files
	aggregatorFilePath = '/modelDependency/aggregator'

	# relative path to MATPOWER distribution
	matpowerDistPath = '/modelDependency/matpower/matpower6.0'

	# transmission system to use
	#matpowerSystem = 'case_WECC240_line_limits_updated'
	matpowerSystem = 'case118'

	# time between power flow solutions in MATPOWER in seconds. OPF need to be a multiple of PF
	matpowerPFTime = 15
	matpowerOPFTime = 300

	# MATPOWER distribution load amplification factor
	matpowerAmpFactor = 25.

	# compile MATPOWER and potentially aggregator wrapper
	wrapperCompile = False

	# create some convenience scripts for running the case
	convenienceScripts = False

	# log levels for the software
	fncsLogLevel = 'WARNING'
	matpowerLogLevel = 'INFO'

	# list of compute resources available for the experiment (ip : [main node [True/False], user [.], experiment path [.], FNCS path [.], GridLAB-D path [.])
	# if you only list one, then the IP field will not be used and you don't have to obtain it!
	#experimentResources = {# '192.168.5.1': [False, rootPath, 'ccsiDemo', fncsExecutablePath, gridlabdExecutablePath],  # Node-5b-18.cybernet.lab
	#						'192.168.5.2': [False, rootPath, 'ccsiDemo', fncsExecutablePath, gridlabdExecutablePath],	# Node-6a-21.cybernet.lab
	#						'192.168.5.3': [False, rootPath, 'ccsiDemo', fncsExecutablePath, gridlabdExecutablePath],	# Node-6b-21.cybernet.lab
	#						'192.168.5.4': [False, rootPath, 'ccsiDemo', fncsExecutablePath, gridlabdExecutablePath], 	# Node-6c-21.cybernet.lab
	#						'192.168.5.5': [True, rootPath, 'ccsiDemo', fncsExecutablePath, gridlabdExecutablePath],	# Node-6d-21.cybernet.lab PORT 2222
	#						'192.168.5.6': [False, rootPath, 'ccsiDemo', fncsExecutablePath, gridlabdExecutablePath]}   # Node-7c-27.cybernet.lab PORT 2223

	experimentResources = {#'172.16.110.40': [False, rootPath, 'ccsiDemo', fncsExecutablePath, gridlabdExecutablePath],  # Node-6a-21.cybernet.lab
						   #'172.16.110.41': [False, rootPath, 'ccsiDemo', fncsExecutablePath, gridlabdExecutablePath],  # Node-6b-21.cybernet.lab
						   #'172.16.110.42': [False, rootPath, 'ccsiDemo', fncsExecutablePath, gridlabdExecutablePath],  # Node-6c-21.cybernet.lab
						   #'172.16.110.43': [True,  rootPath, 'ccsiDemo', fncsExecutablePath, gridlabdExecutablePath],  # Node-6d-21.cybernet.lab PORT 2222
 						   #'172.18.235.70': [False, rootPath, 'ccsiDemo', fncsExecutablePath, gridlabdExecutablePath],  # Node-9a-33.cybernet.lab
						   #'172.18.235.73': [False, rootPath, 'ccsiDemo', fncsExecutablePath, gridlabdExecutablePath],  # Node-9b-33.cybernet.lab
						   #'172.18.235.74': [False, rootPath, 'ccsiDemo', fncsExecutablePath, gridlabdExecutablePath],  # Node-9c-33.cybernet.lab
						   '172.18.235.71': [False, rootPath, 'ccsiDemo', fncsExecutablePath, gridlabdExecutablePath]}  # Node-9d-33.cybernet.lab



	# specify the port fncs will use to communicate on
	fncsPort = '7777'

	# list of distribution systems models and their population distribution for the experiment (feeder : [penetration [%], peakLoad [MW], region [#], control (advanced) [%])
	# inputGLM = {'R1-12.47-1.glm': [1, 7.272, 2]}
	#inputGLM = {'R1-12.47-1.glm' : [0.5, 7, 1, 0],
	# 			'R1-12.47-2.glm' : [0.5, 2, 2, 0.5]}
	# inputGLM = {'4BusSystem.glm': [1, 10]}
	# inputGLM = {'1-12.47-1.glm': [.12, 7.272, 1],
	# 			'R1-12.47-2.glm': [.11, 2.733, 1],
	# 			'R1-12.47-3.glm': [.11, 1.255, 1],
	# 			'R2-12.47-1.glm': [.11, 6.256, 2],
	# 			'R2-12.47-2.glm': [.11, 5.747, 2],
	# 			'R2-12.47-3.glm': [.11, 3.435, 2],
	# 			'R3-12.47-1.glm': [.11, 9.366, 3],
	# 			'R3-12.47-2.glm': [.11, 4.462, 3],
	# 			'R3-12.47-3.glm': [.11, 8.620, 3],}
	
	#inputGLM = {'R1-12.47-1.glm': [.12, 3.5, 1, 1],
	#			'R1-12.47-2.glm': [.11, 1.3, 1, 1],
	#			'R1-12.47-3.glm': [.11, 0.8, 1, 1],
	#			'R2-12.47-1.glm': [.11, 5.0, 2, 1],
	#			'R2-12.47-2.glm': [.11, 3.5, 2, 1],
	#			'R2-12.47-3.glm': [.11, 5.0, 2, 1],
	#			'R3-12.47-1.glm': [.11, 8.0, 3, 1],
	#			'R3-12.47-2.glm': [.11, 4.0, 3, 1],
	#			'R3-12.47-3.glm': [.11, 6.5, 3, 1]}
				
	#inputGLM = {'R1-12.47-1.glm': [.12, 6.5, 1, 1],
	#			'R1-12.47-2.glm': [.11, 6.5, 1, 1],
	#			'R1-12.47-3.glm': [.11, 6.5, 1, 1],
	#			'R2-12.47-1.glm': [.11, 6.5, 2, 1],
	#			'R2-12.47-2.glm': [.11, 6.5, 2, 1],
	#			'R2-12.47-3.glm': [.11, 6.5, 2, 1],
	#			'R3-12.47-1.glm': [.11, 6.5, 3, 1],
	#			'R3-12.47-2.glm': [.11, 6.5, 3, 1],
	#			'R3-12.47-3.glm': [.11, 6.5, 3, 1]}	

	inputGLM = input_data_dict["inputGLM"]
	
	# -------------------------------------------------------------------------------------------
	# ----------------------- No modification beyond this point ---------------------------------
	# -------------------------------------------------------------------------------------------

	# combine path so they are not relative anymore
	feederFilePath = rootPath + feederFilePath
	includeFilePath = rootPath + includeFilePath
	#NRECA EDIT: experimentFilePath now just experimentFilePath pulled directly from json dictionary
	experimentFilePath = experimentFilePath
	matpowerFilePath = rootPath + matpowerFilePath
	aggregatorFilePath = rootPath + aggregatorFilePath
	matpowerDistPath = rootPath + matpowerDistPath

	# some user info
	print 'creating experiment "{:s}" using a total of "{:0.0f}" distribution systems'.format(experimentName, distributionNumber)

	# ensure that the input GLM specification makes sense (i.e percentages sum to one). We only warn the user as it won't break anything
	if abs(sum([inputGLM[key][0] for key in inputGLM.keys()]) - 1) > 0.001:
		print 'WARNING: your distribution system population sums to {:0.2f}, should be 1'.format(sum([inputGLM[key][0] for key in inputGLM.keys()]))

	# We need to create the experiment folder. If it already exists we delete it and then create it
	if os.path.isdir(experimentFilePath + '/' + experimentName):
		print "experiment folder already exists, deleting and moving on..."
		shutil.rmtree(experimentFilePath + '/' + experimentName)
	os.makedirs(experimentFilePath + '/' + experimentName)
	direc=(experimentFilePath + '/' + experimentName)
	# then we need to copy over all the include files for the experiment
	shutil.copytree(includeFilePath + '/players', experimentFilePath + '/' + experimentName + '/include/players')
	shutil.copytree(includeFilePath + '/schedules', experimentFilePath + '/' + experimentName + '/include/schedules')
	shutil.copytree(includeFilePath + '/weather', experimentFilePath + '/' + experimentName + '/include/weather')

	# find the appropiate number of distribution system of each to implement. We need this to create the full distribution system dictionary
	temp = [inputGLM[key][0]*distributionNumber for key in inputGLM.keys()]
	distributionNumberVector = [math.floor(x) for x in temp]
	for remain in xrange(int(distributionNumber - sum(distributionNumberVector))):
		idx = temp.index(max(temp))
		distributionNumberVector[idx] += 1
		temp[idx] = 0

	# create vector with how many of each distribution system should have the ability to attach advanced control
	distributionControlNumberVector = [math.floor(x*inputGLM[inputGLM.keys()[key]][3]) for key, x in enumerate(distributionNumberVector)]

	#print distributionNumberVector
	#print distributionControlNumberVector
	# create the full list of distribution systems to implement (key : {'name' , 'feeder' , 'peakLoad', 'substationkV', 'substationBus', 'fncsSubscriptions'})
	populationDict = {}
	count = 0
	for key, number in enumerate(distributionNumberVector):
		#print 'key master -> ', key
		for keyOffset in xrange(0, int(number)):
			if keyOffset <= distributionControlNumberVector[key]-1:
				advancedControlBool = True
			else:
				advancedControlBool = False	
			populationDict[count] = {'name' : os.path.splitext(inputGLM.keys()[key])[0].replace('-','_').replace('.','_') + '_feeder_' + str(count) ,
											 'feeder' : os.path.splitext(inputGLM.keys()[key])[0],
											 'peakLoad' : inputGLM[inputGLM.keys()[key]][1]*matpowerAmpFactor,
									         'region': inputGLM[inputGLM.keys()[key]][2],
									 		 'advancedControl': advancedControlBool,
									 		 'substationkV' : '',
									 		 'substationBus' : '',
									 		 'fncsSubscriptions' : ''}
			#print 'key offset -> ', keyOffset, 'control -> ',advancedControlBool
			count += 1

	# some user info
	#print 'creating MATPOWER simulator'

	# this function will add the transmission system to our co-simulation
	#populationDict = coSimConfiguration.createMATPOWERSystem(populationDict, experimentFilePath, experimentName, matpowerFilePath, matpowerDistPath, matpowerSystem, matpowerAmpFactor, matpowerPFTime, date_list)

	# it is assumed that the list of feeders will be much less than the actual amount of distribution system.
	# instead of parsing the same system over an over we will parse all of them once.
	parsedDict = {}
	for feeder in inputGLM:
		# Parse the feeder model into a nice dictionary
		originalGLM = parseGLM.parse(feederFilePath + '/' + feeder)
		parsedDict[os.path.splitext(feeder)[0]] = originalGLM

	# create all the distirbution systems
	l = multiprocessing.Lock()
	pool = multiprocessing.Pool(initializer=coSimConfiguration.initLock, initargs=(l,), processes=multiprocessing.cpu_count())
	poolResults = []
	for randomSeed, feeder in enumerate(populationDict):
		# print populationDict[feeder]

		# pool.apply(coSimConfiguration.createDistributionSystem, args=(parsedDict[populationDict[feeder]['feeder']], experimentFilePath, experimentName, populationDict[feeder]['feeder'], populationDict[feeder]['name'], populationDict[feeder]['substationkV'], populationDict[feeder]['substationBus'], populationDict[feeder]['fncsSubscriptions'], randomSeed, ))
		# pool.apply_async(coSimConfiguration.createDistributionSystem, args=(parsedDict[populationDict[feeder]['feeder']], experimentFilePath, experimentName, populationDict[feeder]['feeder'], populationDict[feeder]['name'], populationDict[feeder]['substationkV'], populationDict[feeder]['substationBus'], populationDict[feeder]['fncsSubscriptions'], randomSeed, ), callback=poolResults.append)
		pool.apply_async(coSimConfiguration.createDistributionSystem, args=(parsedDict[populationDict[feeder]['feeder']], experimentFilePath, experimentName, populationDict[feeder], randomSeed, date_list), callback=poolResults.append)
		# coSimConfiguration.createDistributionSystem(parsedDict[populationDict[feeder]['feeder']], experimentFilePath, experimentName, populationDict[feeder]['feeder'], populationDict[feeder]['name'], populationDict[feeder]['substationkV'], populationDict[feeder]['substationBus'], populationDict[feeder]['fncsSubscriptions'], randomSeed)

	# code to show the user progress in creating the experiment
	print 'creating distribution systems'
	time.sleep(1) # seems to be needed
	pbar = tqdm.tqdm(desc='processing',total=len(populationDict.keys()), bar_format='{desc}|{bar}| {percentage:3.0f}%', ncols=50)
	oldLen = 0
	updateLeft = len(populationDict.keys())
	while len(poolResults) != len(populationDict.keys()):
		updateLeft -= len(poolResults)-oldLen
		pbar.update(len(poolResults)-oldLen)
		oldLen = len(poolResults)
		time.sleep(1)
	pbar.update(updateLeft)
	pbar.close()

	# ensure that all workers are finished before we continue
	pool.close()
	pool.join()

	# some user info
	print 'creating convenience scripts'

	# we need to determine the simulation time as it is required by the MATPOWER wrapper
	feederConfig, _ = feederConfiguration.feederConfiguration(populationDict[populationDict.keys()[0]]['feeder'], date_list)
	matpowerFullTime = int((datetime.datetime.strptime(feederConfig['stopdate'], '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(feederConfig['startdate'], '%Y-%m-%d %H:%M:%S')).total_seconds())

	# this function will create some convenience scripts for running the cases
	if convenienceScripts:
		coSimConfiguration.createConvenienceScripts(populationDict, experimentResources, matpowerFilePath, aggregatorFilePath, experimentFilePath, experimentName, matpowerSystem, matpowerOPFTime, matpowerAmpFactor, matpowerFullTime, matpowerLogLevel, fncsLogLevel, date_list, fncsPort)

	# this will compile the MATPOWER wrapper if the user specified this in the options
	if wrapperCompile:
		coSimConfiguration.compileWrappers(matpowerFilePath, aggregatorFilePath, experimentFilePath, experimentName, fncsExecutablePath, matlabExecutablePath, zeroMQLibraryPath, CZMQLibraryPath, date_list)

	end = time.time()
	print 'successfully completed experiment creation in {:0.1f} seconds'.format(end - start)


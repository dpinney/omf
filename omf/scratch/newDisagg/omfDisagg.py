''' 

Use new solar disagg code to in an 'omf model' style script for potly output as like current solar disagg version.

'''

import time, csv, pickle
from os.path import join as pJoin
#from omf.models import __neoMetaModel__

#SolarDisagg imports
import numpy as np
import pandas as pd
from decimal import *
import scipy as sc

# OMF imports
from omf.scratch.newDisagg import CSSS
#sys.path.append(__neoMetaModel__._omfDir)
#from omf.weather import pullAsos
#from omf.solvers.newCSSS import CSSS
#from CSSS import CSSS

# Model metadata:
#modelName, template = metadata(__file__)
#modelName = 'newSolarDisagg'
#hidden = True

def work():

	#plotly imports
	import plotly
	from plotly import __version__
	from plotly.offline import download_plotlyjs, plot
	from plotly import tools
	import plotly.graph_objs as go
	''' Run the model in its directory. '''
	# Delete output file every run if it exists
	outData = {}		
	# Model operations goes here.

	'''TODO
	Replace meters with single numpy array for reactive total power
	'''
	#read measured load from csv file
	def buildMat(df,numD,dfName,normFact,windH,intercept):
	    N=len(df)
	    X = np.array(df[dfName]/normFact) # vector data to organize in appropriate form
	    numW = len(windH) # number of windows
	    Xbig = [[[] for i in range(numW)] for j in range(numD)]

	    # Loop through X vector and create Xbig matrix
	    initStep = pd.to_datetime(df['Unnamed: 0'].iloc[0])
	    initDay = initStep.day

	    for i in range(N):
	        curStep = pd.to_datetime(df['Unnamed: 0'].iloc[i])
	        curDay = curStep.day - initDay
	        curHour = curStep.hour

	        indices = np.where(curHour-np.array(windH)>=0)
	        curWind = indices[0][len(indices[0])-1]

	        Xbig[curDay][curWind].append(X[i])

	    # Build Xhat matrix (which multiplies the vector of time-varying regressors) using Xbig
	    for i in range(numD):
	        Xaux = []
	        for j in range(numW):
	            tmp = np.array(Xbig[i][j]) 
	            tmplen = len(tmp)
	            tba = tmp.reshape((tmplen,1)) # to be added
	            if j==0:
	                Xaux = tba
	                Iaux = np.ones((tmplen,1))
	            else:       
	                Xaux = sc.linalg.block_diag(Xaux,tba)
	                Iaux = sc.linalg.block_diag(Iaux,np.ones((tmplen,1)))
	        if i==0:
	            Xtilda = Xaux
	            Itilda = Iaux
	        else:
	            Xtilda = np.vstack((Xtilda,Xaux))
	            Itilda = np.vstack((Itilda,Iaux))
	    if (intercept):
	        Xhat = np.hstack((Itilda,Xtilda))
	    else:
	        Xhat = Xtilda
	    return Xhat


	# In[3]:


	## Organises X data from df in appropriate matrix form (Xhat) to support optimization with time-varying regressors
	# The function assumes the the regressors are of the form Y_i = X_i * k_i + R_i, where k_i and R_i are scalars and i indicates one time window
	# Matrix notation for all time windows: Y = Xhat * [R; k]. Structure of Xhat = [blkdiag(ones_vectors) | blkdiag(Xaux)]
	# This version is WITH weekday-weekend dependence
	def buildMat2(df,numD,dfName,normFact,windH,intercept):
	    N=len(df)
	    X = np.array(df[dfName]/normFact) # vector data to organize in appropriate form
	    numW = len(windH) # number of windows
	    dayOfWeek = np.array(df['dayOfWeekIndex'])
	    Xbig = [[[] for i in range(numW)] for j in range(numD)]
	    dayOfWeekBig = [[[] for i in range(numW)] for j in range(numD)]

	    # Loop through X vector and create Xbig matrix
	    initStep = pd.to_datetime(df['Unnamed: 0'].iloc[0])
	    initDay = initStep.day

	    for i in range(N):
	        curStep = pd.to_datetime(df['Unnamed: 0'].iloc[i])
	        curDay = curStep.day - initDay
	        curHour = curStep.hour

	        indices = np.where(curHour-np.array(windH)>=0)
	        curWind = indices[0][len(indices[0])-1]

	        Xbig[curDay][curWind].append(X[i])
	        dayOfWeekBig[curDay][curWind].append(dayOfWeek[i])

	    # Build Xhat matrix (which multiplies the vector of time-varying regressors) using Xbig
	    for i in range(numD):
	        Xaux = []
	        for j in range(numW):
	            tmp = np.array(Xbig[i][j]) 
	            tmplen = len(tmp)
	            tba = tmp.reshape((tmplen,1)) # to be added
	            if j==0:
	                Xaux = tba
	                Iaux = np.ones((tmplen,1))
	            else:       
	                Xaux = sc.linalg.block_diag(Xaux,tba)
	                Iaux = sc.linalg.block_diag(Iaux,np.ones((tmplen,1)))
	        Xaux2 = np.hstack((Xaux,np.zeros(Xaux.shape)))
	        Iaux2 = np.hstack((Iaux,np.zeros(Iaux.shape)))
	        Xaux3 = np.hstack((np.zeros(Xaux.shape),Xaux))
	        Iaux3 = np.hstack((np.zeros(Iaux.shape),Iaux))
	        
	        if i==0:
	            if ((dayOfWeekBig[i][j][0]!=5) and (dayOfWeekBig[i][j][0]!=6)): #weekdays
	                Xtilda = Xaux2
	                Itilda = Iaux2
	            else: # weekends
	                Xtilda = Xaux3
	                Itilda = Iaux3
	                                   
	        else:
	            if ((dayOfWeekBig[i][j][0]!=5) and (dayOfWeekBig[i][j][0]!=6)): #weekdays
	                Xtilda = np.vstack((Xtilda,Xaux2))
	                Itilda = np.vstack((Itilda,Iaux2))
	            else:
	                Xtilda = np.vstack((Xtilda,Xaux3))
	                Itilda = np.vstack((Itilda,Iaux3))
	    if (intercept):
	        Xhat = np.hstack((Itilda,Xtilda))
	    else:
	        Xhat = Xtilda
	    return Xhat


	# In[4]:


	# Shorthand for adding standard constraints in the CSSS problem
	def standardConst(df,csss,name1,name2):
	    # Constrain Solar to be <= 0 . 
	    csss.addConstraint(csss.models[name1]['source'] <= 0 )
	    # Constrain Load to be >=0
	    csss.addConstraint(csss.models[name2]['source'] >= 0 )
	    # Constraint Solar to be 0, when solar proxy is 0
	    irrProxy = df['IrradianceProxy']
	    idx0 = np.where(irrProxy<1)[0]
	    csss.addConstraint(csss.models[name1]['source'][idx0] == 0 )
	    return csss    

	# Shorthand for adding sign constraints for source signals in the CSSS problem
	def signConst(csss,name1,name2):
	    # Constrain Solar to be <= 0 . 
	    csss.addConstraint(csss.models[name1]['source'] <= 0 )
	    # Constrain Load to be >=0
	    csss.addConstraint(csss.models[name2]['source'] >= 0 )
	    return csss

	# Shorthand for adding sign constraints for source signals and regressors in the CSSS problem
	def signConst2(csss,name1,name2):
	    # Constrain Solar to be <= 0 . 
	    csss.addConstraint(csss.models[name1]['source'] <= 0 )
	    # Constrain Load to be >=0
	    csss.addConstraint(csss.models[name2]['source'] >= 0 )
	    # Constrain solar regressors to be <= 0
	    csss.addConstraint(csss.models[name1]['theta'] <= 0 )
	    # Constrain load regressors to be >= 0
	    csss.addConstraint(csss.models[name2]['theta'] >= 0 )
	    return csss

	# Sign constraints 2 + constrain some of the time-varying regressors to be constant
	def signConst2AndRegConst(csss,name1,name2,regressor,linearThetaConst,intercThetaConst):
	    # Constrain Solar to be <= 0 . 
	    csss.addConstraint(csss.models[name1]['source'] <= 0 )
	    # Constrain Load to be >=0
	    csss.addConstraint(csss.models[name2]['source'] >= 0 )
	    # Constrain solar regressors to be <= 0
	    csss.addConstraint(csss.models[name1]['theta'] <= 0 )
	    # Constrain load regressors to be >= 0
	    csss.addConstraint(csss.models[name2]['theta'] >= 0 )
	    # Constrain time-varying linear coefficients of load model to be equal
	    nReg = regressor.shape[1]
	    if nReg>=2:
	        if (linearThetaConst):
	            for i in range(int(nReg/2),int(nReg-1)):
	                csss.addConstraint(csss.models[name2]['theta'][i]==csss.models[name2]['theta'][i+1])
	        if (intercThetaConst):
	            for i in range(int(nReg/2-1)):
	                csss.addConstraint(csss.models[name2]['theta'][i]==csss.models[name2]['theta'][i+1]) 
	    else:
	        pass
	    return csss

	# Shorthand for collecting results from optimization
	def collectRes(csss,name):
	    res = []
	    for val in csss.models[name]['source'].value:
	        res.append(float(val))
	    return res

	# Filter only part of data during daytime (exclude night)
	def excludeNight(df):
	    irrProxy = df['IrradianceProxy']
	    idx0 = np.where(irrProxy>=1)[0]
	    df_new = df.iloc[idx0]
	    return df_new

	# Identify indices where the day change occurs --> relevant for source regularization
	#Needed for model
	def findDayChng(df):
	    dayIndex = df['DayIndex']
	    idx = np.where(np.diff(dayIndex)!=0)[0]
	    return idx

	def getTestSet(df,testRatio,seed):
	    dayIndex = df['DayIndex']
	    firstDay = np.min(dayIndex)
	    lastDay = np.max(dayIndex)
	    numDays = lastDay-firstDay+1
	    allDays = np.arange(firstDay,lastDay+1)
	    numTestDays = int(np.ceil(testRatio*numDays))
	    testSet = []
	    np.random.seed(seed)
	    for i in range(numTestDays):
	        toInsert = int(np.round(np.random.uniform(firstDay,lastDay)))
	        while toInsert in testSet:
	            toInsert = int(np.round(np.random.uniform(firstDay,lastDay)))
	        testSet.append(toInsert)
	    trainSet = np.setdiff1d(allDays,testSet)
	    return trainSet, np.sort(testSet)

	# Split dataframe into training and validation set
	def splitDFinto2DFs(df,trainSet,testSet):
	    dayIndex = df['DayIndex']
	    
	    idxTrain = []
	    for day in trainSet: 
	        tmp = np.where(dayIndex==day)[0]
	        idxTrain = np.concatenate((idxTrain,tmp))
	    df_train = df.iloc[idxTrain]
	    
	    idxTest = []
	    for day in testSet: 
	        tmp = np.where(dayIndex==day)[0]
	        idxTest = np.concatenate((idxTest,tmp))
	    df_test = df.iloc[idxTest]
	    return df_train, df_test 

	# Find the hour indexes when solar irradiance is > 0
	def minAndMaxPVhours(df):
	    N=len(df)
	    minHour = np.inf
	    maxHour = -np.inf
	    for i in range(N):
	        curStep = pd.to_datetime(df['Unnamed: 0'].iloc[i])
	        curHour = curStep.hour
	        minHour = np.minimum(curHour,minHour)
	        maxHour = np.maximum(curHour,maxHour)
	    maxHour+=1
	    return minHour,maxHour
	    


	# In[5]:


	## Error metric definitions
	def mae(x,y):
	    N = len(x)
	    return (np.sum(np.absolute(y-x)))/N

	def rmse(x,y):
	    N = len(x)
	    return np.sqrt((np.sum(np.square(y-x)))/N)


	# # Import the data for the distributed PV case

	# In[6]:


	monthUsed = 'August' # 'January' or 'August'
	'''
	if monthUsed == 'January':
	    df = pd.read_csv('Sample_Jan_data.csv')
	elif monthUsed == 'August':
	    df = pd.read_csv('Sample_Aug_data.csv')

	else:
	    raise NameError('No suitable selection of month!')

	df=df.dropna()
	N=len(df)

	# Reset index of power-data df to datetime --> relevant only when adding airport irradiance data
	#This is captured in the solardisagg weathe df
	df['Time'] = pd.to_datetime(df['Unnamed: 0'])
	df = df.reset_index().set_index('Time')

	Pagg = np.array(df['Real_Power_Total'])
	Qagg = np.array(df['Reactive_Power_Total'])

	#this is the solar
	df['IrradianceProxy1']= df['System 4'] # PV system with South orientation as irradiance proxy
	# df['IrradianceProxy1']= df['System 2'] # PV system with South-West orientation as irradiance proxy
	# df['IrradianceProxy1']= df['System 1'] # PV system with South-East orientation as irradiance proxy
	df['IrradianceProxy'] = df['IrradianceProxy1']

	# Add the day number - easy calc to add
	# Extend the data frame with a column that includes the day number
	dayIndex = [pd.to_datetime(df['Unnamed: 0'].iloc[i]).day for i in range(len(df))] 
	df['DayIndex'] = dayIndex

	#Add day of week number - easy to add
	# Extend the data frame with a column that indicates the day of the week (6 is Sunday)
	dayOfWeekIndex = pd.to_datetime(df['Unnamed: 0']).dt.dayofweek
	df['dayOfWeekIndex'] = dayOfWeekIndex
	'''
	reactivePowerDataFile = "reactivePowerLBNL.csv"
	solarDataFile = "solarLBNL.csv"
	realPowerDataFile = "realPowerLBNL.csv"
	latLonDataFile = "lat_lon_data_plus.csv"
	weatherDataFile = "weatherLBNL.csv"

	reactive_power_csv = []
	#with open(pJoin(modelDir, inputDict['reactivePowerFileName']),'w') as loadTempFile:
	#	loadTempFile.write(inputDict['reativePowerData'])
	try:
		with open(reactivePowerDataFile, newline='') as csvfile:
			#csvreader = csv.reader(csvfile, delimiter=',')
			#meterNames = next(csvreader)
			csvreader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
			for row in csvreader:
				reactive_power_csv.append(row)
	except:
		errorMessage = 'CSV file is incorrect format.'
		raise Exception(errorMessage)
	#reactive_power_csv = np.array(reactive_power_csv)
	reactive_power_csv = [y for x in reactive_power_csv for y in x]

	#read the solar proxy from csv file
	solarproxy_csv = []
	#with open(pJoin(modelDir, inputDict['solarFileName']),'w') as loadTempFile:
	#	loadTempFile.write(inputDict['solarData'])
	try:
		with open(solarDataFile, newline='') as csvfile:
			csvreader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
			for row in csvreader:
				solarproxy_csv.append(row)
	except:
		errorMessage = "CSV file is incorrect format."
		raise Exception(errorMessage)
	solarproxy_csv = [y for x in solarproxy_csv for y in x]

	real_power_csv = []
	#with open(pJoin(modelDir, inputDict['realPowerFileName']),'w') as loadTempFile:
	#	loadTempFile.write(inputDict['realPowerData'])
	try:
		with open(realPowerDataFile, newline='') as csvfile:
			csvreader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
			for row in csvreader:
				real_power_csv.append(row)
	except:
		errorMessage = 'CSV file is incorrect format.'
		raise Exception(errorMessage)
	real_power_csv = [y for x in real_power_csv for y in x]

	#read the solar proxy from csv file
	weather_csv = []
	#with open(pJoin(modelDir, inputDict['weatherFileName']),'w') as loadTempFile:
	#	loadTempFile.write(inputDict['weatherData'])
	try:
		with open(weatherDataFile, newline='') as csvfile:
			csvreader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
			for row in csvreader:
				weather_csv.append(row)
	except:
		errorMessage = "CSV file is incorrect format."
		raise Exception(errorMessage)
	weather_csv = [y for x in weather_csv for y in x]

	df=pd.read_csv('dateLBNL.csv').dropna()
	df['Time'] = pd.to_datetime(df['Unnamed: 0'])
	df = df.reset_index().set_index('Time')
	N=len(df)
	df['Temp(int)'] = np.array(weather_csv)
	df['Real_Power_Total'] = real_power_csv
	df['Reactive_Power_Total'] = reactive_power_csv
	df['IrradianceProxy'] = solarproxy_csv
	# Add the day number - easy calc to add
	# Extend the data frame with a column that includes the day number
	dayIndex = [pd.to_datetime(df['Unnamed: 0'].iloc[i]).day for i in range(len(df))] 
	df['DayIndex'] = dayIndex

	#Add day of week number - easy to add
	# Extend the data frame with a column that indicates the day of the week (6 is Sunday)
	dayOfWeekIndex = pd.to_datetime(df['Unnamed: 0']).dt.dayofweek
	df['dayOfWeekIndex'] = dayOfWeekIndex

	# In[7]:


	# Create dataframe with orientations
	'''
	dfOrient = pd.read_csv('Orientation_data.csv')

	SWnum = len(dfOrient.loc[dfOrient['Orien']=='South;West'])
	Snum = len(dfOrient.loc[dfOrient['Orien']=='South'])
	Wnum = len(dfOrient.loc[dfOrient['Orien']=='West'])
	WEnum = len(dfOrient.loc[dfOrient['Orien']=='West;East'])
	SEnum = len(dfOrient.loc[dfOrient['Orien']=='South;East'])
	Enum = len(dfOrient.loc[dfOrient['Orien']=='East'])
	totnum = len(dfOrient)'''


	# Take out night time from whole dataframe
	df = excludeNight(df)
	#N=len(df)

	#Pagg = np.array(df['Real_Power_Total'])
	#Qagg = np.array(df['Reactive_Power_Total'])
	#Irp = df['IrradianceProxy']

	#solarAct = -1*df['Real_Power_PV']
	#loadAct = df['Real_Power_Total']+df['Real_Power_PV']

	# Identify indices where the day change occurs --> relevant for source regularization
	idxDayChange = findDayChng(df)
	idxDayChange = idxDayChange+1 # add one due to the 0-indexing in Python

	#avgLoadPower = np.mean(loadAct)

	saveRes = False
	plotRes = False
	proxyLim = 1 # maximum number of proxies to simulate with. In the range [1,len(proxyIDdict.keys())]

	# Define data set
	dfAux = df
	N = len(dfAux)
	idxDayChangeAux = idxDayChange
	#solarActAux = solarAct
	#loadActAux = loadAct
	#PVinstalled = 7500 # in kW

	#TODO: Auto calculate in model
	numDays = 31
	minHour, maxHour = minAndMaxPVhours(dfAux) # minimum and maximum sunshine hours
	pvDur = maxHour-minHour

	#TODO use solar input instead of pickle
	#pickle_in = open("proxyIDdict.pickle","rb")
	#proxyIDdict = pickle.load(pickle_in) # dict with PV systems used as proxies for each scenario of number of proxies

	#TODO Change this, not needed, but needed to run sim
	month = monthUsed
	simCases = ['E'] #['A','B','C','D','E']

	#TODO figure out what values to use here
	if month=='January': 
	    alphaVal = 5
	    gammaVal = 5
	    betaVal = 0
	else:
	    alphaVal = 1
	    gammaVal = 1.5
	    betaVal = 10**6
	    
	for simCase in simCases:
	    if (simCase=='A') | (simCase=='B') | (simCase=='C'):
	        Qaux = np.vstack((np.ones((1,N)),np.array(dfAux['Reactive_Power_Total']))).transpose()
	    elif (simCase=='D'):
	        Qaux = np.vstack((np.ones((1,N)),np.array(dfAux['Reactive_Power_Total']),np.array(dfAux['Temp(int)']))).transpose()
	    elif (simCase=='E'):
	        numWind = 1 
	        windStep = pvDur/numWind
	        windEdges = [minHour+k*windStep for k in range(numWind)]
	        Qaux1 = buildMat2(dfAux,numDays,'Reactive_Power_Total',1,windEdges,True)
	        Qaux2 = buildMat2(dfAux,numDays,'Temp(int)',1,windEdges,False)
	        Qaux = np.hstack((Qaux1,Qaux2))
	windStep = pvDur/numWind
	windEdges = [minHour+k*windStep for k in range(numWind)]
	Iraux = buildMat(dfAux,numDays,'IrradianceProxy',1,windEdges,False)
	N=len(dfAux)
	CSSS_solar = CSSS.CSSS(np.array(dfAux['Real_Power_Total']))
	#print(Qaux.shape)
	#print(Iraux.shape)
	if (simCase=='A'):
	    CSSS_solar.addSource(Qaux,alpha=alphaVal,name='Load',costFunction='l1')
	    CSSS_solar.addSource(Iraux,alpha=1,name='Solar',costFunction='l1')
	elif (simCase=='B'):
	    CSSS_solar.addSource(Qaux,alpha=alphaVal,name='Load',costFunction='l1',regularizeTheta='l2',beta=0,regularizeSource='diff_l1',gamma=gammaVal,idxScrReg=idxDayChangeAux)
	    CSSS_solar.addSource(Iraux,alpha=1,name='Solar',costFunction='l1',regularizeTheta='l2',beta=0,regularizeSource='diff_l1',gamma=0,idxScrReg=idxDayChangeAux)
	elif (simCase=='C') | (simCase=='D') | (simCase=='E'):
	    CSSS_solar.addSource(Qaux,alpha=alphaVal,name='Load',costFunction='l1',regularizeTheta='l2',beta=0,regularizeSource='diff_l1',gamma=gammaVal,idxScrReg=idxDayChangeAux)
	    CSSS_solar.addSource(Iraux,alpha=1,name='Solar',costFunction='l1',regularizeTheta='diff_l1',beta=betaVal,numWind=numWind)

	#CSSS_solar = signConst(CSSS_solar,'Solar','Load')
	CSSS_solar = signConst2(CSSS_solar,'Solar','Load')

	start=time.time()
	a=CSSS_solar.constructSolve('ECOS',False)
	optTime = time.time()-start
	print("It took {} seconds to solve the CSSS problem".format(optTime))

	solarDisag = []
	for val in CSSS_solar.models['Solar']['source'].value:
	    solarDisag.append(float(val))
	loadDisag = []
	for val in CSSS_solar.models['Load']['source'].value:
	    loadDisag.append(float(val))
	solarPlotData = go.Scatter(y=np.array([item for sublist in CSSS_solar.models['Solar']['source'].value.tolist() for item in sublist]),x=dfAux.index, name=('Disaggregated PV'), marker=dict(color='gold'))
	loadPlotData = go.Scatter(y=np.array([item for sublist in CSSS_solar.models['Load']['source'].value.tolist() for item in sublist]),x=dfAux.index, name=('Disaggregated Load'), marker=dict(color='blue'))
	actualLoadData = go.Scatter(y=np.array(dfAux['Real_Power_Total'])+np.array(dfAux['Reactive_Power_Total']),x=dfAux.index, name=('Actual Load'), marker=dict(color='green'))
	plotData = [solarPlotData, loadPlotData, actualLoadData]
	fig = go.Figure(data=plotData)
	plot(fig)

if __name__ == '__main__':
	work()
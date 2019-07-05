import matplotlib.pyplot as plt
import __neoMetaModel__
import json
from __neoMetaModel__ import *
import numpy as np
import datetime
import csv
import pandas as pd
from dateutil import parser
import os
import shutil
import re
import warnings
import itertools
import plotly.graph_objs as go
from plotly import tools
import plotly.offline
from scipy.stats import linregress
from sklearn import preprocessing
from sklearn.metrics import confusion_matrix
from zipfile import ZipFile
from base64 import b64encode, b64decode

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "Identifies true meter phases by comparing AMI and SCADA data."
hidden = True

def unzip(zipdir, target):
	with ZipFile(zipdir, 'r') as zip:
		# zip.printdir()
		shutil.rmtree(target, ignore_errors=True)
		os.mkdir(target)
		zip.extractall(path=target)
	# remove empty '_MACOSX' folder generated after extraction under MAC OS
	MAC_OSX_path = os.path.join(target, '__MACOSX')
	if os.path.exists(MAC_OSX_path):
		os.rmdir(MAC_OSX_path)

def file_transform_gld(METER_DIR, SUB_METER_FILE):
	''' This function transform the original Meter and substation voltage files from GridLAB-D to
	... more neat form. More specifically, change all polar or rectangular
	... form of voltage to magnitude'''
	def get_hour(startyear, endTime):
		''' Helper to calculate hour count. '''
		hour = (endTime - datetime.datetime(startyear, 1,1)).days*24
		return hour
	startTime = datetime.datetime(2014, 1, 1)
	endTime = datetime.datetime(2015, 1, 1)
	startHour = get_hour(startTime.year, startTime)
	endHour = get_hour(startTime.year, endTime)
	times = np.genfromtxt(SUB_METER_FILE, delimiter=",", usecols=0, skip_header=9, dtype=str)
	# 8784-24 = 8760 since original data ends at 2015-01-01 23:00:00 EST
	times2 = list(times[0:8760])
	filelist = ['./{}/'.format(METER_DIR) + f for f in os.listdir(METER_DIR) if f.endswith('.csv')] + [SUB_METER_FILE]
	for file in filelist:
		vals_ij = np.genfromtxt(file, delimiter=",",usecols=[2,3,4], skip_header = 9, dtype=str)
		vals_ij = np.transpose(vals_ij)
		mags = []
		for column in vals_ij:
			if 'kV' in column[0] and 'kVA' not in column[0]:
				try:
					mag = []
					for volt in column[startHour:endHour]:
						if 'i' in volt or 'j' in volt:
							mag.append(abs(complex(volt.replace(' kV', '').replace('i', 'j'))))
						elif 'd' in volt:
							mag.append(float(volt.replace('-','+').split('+')[1]))
					mags.append(mag)
				except ValueError:
					pdb.set_trace()
		mags = [[np.round(float(i), 4) for i in nested] for nested in mags]
		v_dic = {'Timestamp': times2, 'V_A': mags[0], 'V_B': mags[1],'V_C': mags[2]}
		df_v = pd.DataFrame(v_dic)
		filetype = file.split('.')[-2].split('_')[-2] #split the string to get either 'meter' or 'node'
		if filetype == 'meter':
			meter_index = file.split('.')[-2].split('_')[-1]
			meterV = 'Meter_%d.csv'%int(meter_index)
			newdir = os.path.join(modelDir, 'Revised Meter Voltage Files')
			if not os.path.exists(newdir):
				os.makedirs(newdir)
			file_path = os.path.join(newdir, meterV)
		elif filetype == 'node':
			newdir = os.path.join(modelDir, 'Revised Substation Voltage Files')
			if not os.path.exists(newdir):
				os.makedirs(newdir)
			file_path = os.path.join(newdir, file)
		else:
			pass
		df_v.to_csv(file_path, header=True, index=False, sep=',', mode='w')

def work(modelDir, inputDict):
	""" Run the model in its directory."""
	outData = {}
	# write input file to modelDir sans carriage returns
	with open(pJoin(modelDir, "rec_sub_meter.csv"), "w") as subFile:
		subFile.write(inputDict["subMeterData"].replace("\r", ""))
	with open(pJoin(modelDir, "meters_transformed.zip"), "w") as meterZip:
		meterZip.write(b64decode(inputDict["meterZip"]))
	# Voltage data transformation and preparation 
	# This chunk take about 10 sec to run
	GLD = False
	METER_DIR = 'Temp Unzipped Data'
	if GLD:
		ZIP_FILE = 'meters_gld.zip'
		SUB_METER_FILE = 'rec_R1-12-47-3_node_53.csv'
		unzip(ZIP_FILE, 'Temp Unzipped Data')
		file_transform_gld(pJoin(modelDir, METER_DIR), pJoin(modelDir, SUB_METER_FILE))
		ssdir = os.path.join(modelDir, 'Revised Substation Voltage Files', SUB_METER_FILE)
	else:
		ZIP_FILE = 'meters_transformed.zip'
		SUB_METER_FILE = 'rec_sub_meter.csv'
		unzip(pJoin(modelDir, ZIP_FILE), pJoin(modelDir, 'Revised Meter Voltage Files'))
		ssdir = os.path.join(modelDir, SUB_METER_FILE)
	# Perform linear regression and make output csv file.
	# Read transformed files and perform regression
	# Ignore scipy warnings.
	warnings.filterwarnings('ignore', category=RuntimeWarning)
	df_ss = pd.read_csv(ssdir)
	min_max_scaler = preprocessing.MinMaxScaler()
	df_ss[['V_A', 'V_B', 'V_C']] = min_max_scaler.fit_transform(df_ss[['V_A', 'V_B', 'V_C']])
	newdir = os.path.join(modelDir, 'Revised Meter Voltage Files')
	meters = os.listdir(newdir)
	 # sort meter names based on number
	meters = sorted(meters, key=lambda x: int(re.sub('\D', '', x)))
	# meters.remove('Meter_22.csv') # this is power-bus meter, I would not consider it.
	# perform voltage correlation between meter voltage and substation voltage
	# to make predictions for meter phase. Finally, it writes the the result to an csv file.
	volt = ['V_A','V_B','V_C']
	result_path = pJoin(modelDir, 'output-regression-result.csv')
	# write the header of the output csv file
	with open(result_path, 'w') as f:   
		f.write('Meter Name,M_A ~ SS_A,M_A ~ SS_B,M_A ~ SS_C, M_B ~ SS_A,M_B ~ SS_B,M_B ~ SS_C,'                +'M_C ~ SS_A,M_C ~ SS_B,M_C ~ SS_C,Input Phase,Predicted Phase\n')
	# read and scale the transformed meter files
	for meter in meters:
		meterdir = os.path.join(newdir, meter)
		df_m = pd.read_csv(meterdir)        
		# MinMaxScaler scale the number to (0,1) without distort the characteristics of original data
		min_max_scaler = preprocessing.MinMaxScaler() 
		df_m[['V_A', 'V_B', 'V_C']] = min_max_scaler.fit_transform(df_m[['V_A', 'V_B', 'V_C']])
		# check the scaled data, only print first 4 rows of each file
		#print meter
		#print df_m.iloc[1:5,:]
		#print '========================='
		#list to store R^2 value
		rr_list = [] 
		# this is a temp list to store R^2 values of each meter. This is appended to rr_list during each iteration.
		phase_rr = []
		# double for loop to perform voltage correlation
		for v1 in volt:
			v_meter_rgre = df_m[v1]
			if phase_rr:
				phase_rr = [round(i, 3) for i in phase_rr]
				rr_list.append(phase_rr)
				phase_rr = []
			for v2 in volt:
				v_ss_rgre = df_ss[v2]
				r = list(linregress(v_meter_rgre,v_ss_rgre))[2]
				rsqre = r**2
				phase_rr.append(rsqre)
		phase_rr = [round(i, 3) for i in phase_rr] 
		rr_list.append(phase_rr)
		sum_rr = [] # store the sum R^2 value in all sublists.
		count = 0 # this represent number of non-zero phases.
		for ls in rr_list:
			sum_rr.append(sum(ls))
			if sum(ls) == 0:
				count = count + 1
		phase_pred = []
		if count == 0:
			actual_ph = 'ABC'
			for rr in rr_list:
				max_index = rr.index(max(rr))
				if max_index == 0:
					phase_pred.append('A')
				elif max_index == 1:
					phase_pred.append('B')
				else:
					phase_pred.append('C')
			ph_out = phase_pred[0]+phase_pred[1]+phase_pred[2]
		elif count == 2:
			ph_temp = ['A','B','C']
			sum_rr_i = [i for i, e in enumerate(sum_rr) if e!=0][0] # get the index of non-zero value
			actual_ph = ph_temp[sum_rr_i]
			rr = rr_list[sum_rr_i]
			max_index = rr.index(max(rr))
			if max_index == 0:
				phase_pred.append('A')
			elif max_index == 1:
				phase_pred.append('B')
			else:
				phase_pred.append('C')
			ph_out = phase_pred[0]
		else:
			pass
		with open(result_path, 'a') as f:
			# write the header of the outfile
			f.write('%s,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%s,%s\n'%(meter,rr_list[0][0], rr_list[0][1], rr_list[0][2], rr_list[1][0], rr_list[1][1], rr_list[1][2],rr_list[2][0], rr_list[2][1],rr_list[2][2],actual_ph,ph_out))
	# basic confusion matrix form sklearn
	result_path = pJoin(modelDir, 'output-regression-result.csv')
	df_final = pd.read_csv(result_path)
	y_true = df_final['Input Phase']
	y_pred = df_final['Predicted Phase']
	classes=['A', 'B','C', 'ABC']
	confusion_matrix(y_true, y_pred, labels=['A', 'B', 'C','ABC'])
	# modified confusion matrix from self-defined function
	cnf_matrix = confusion_matrix(y_true, y_pred, labels=['A', 'B','C', 'ABC'])
	np.set_printoptions(precision=2)
	plt.figure(dpi=200, figsize=(10,5))
	plt.grid(b=False)
		# Confusion Matrix Generation
	def plot_confusion_matrix(
			cm,
			classes,
			cmap=plt.cm.Blues
		):
		'''Self-defined function for better illustrating confusion matrix.'''
		plt.imshow(cm, interpolation='nearest', cmap=cmap, aspect='auto')
		plt.colorbar()
		tick_marks = np.arange(len(classes))
		plt.xticks(tick_marks, classes, rotation=45)
		plt.yticks(tick_marks, classes)
		fmt = 'd'
		thresh = cm.max() / 2.
		for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
			plt.text(j, i, format(cm[i, j], fmt),
					horizontalalignment="center",
					color="white" if cm[i, j] > thresh else "black")
		plt.ylabel('Input Label')
		plt.xlabel('Predicted Label')
		plt.tight_layout()
	plot_confusion_matrix(cnf_matrix, classes=['A', 'B', 'C','ABC'])
	plt.savefig(pJoin(modelDir,'output-conf-matrix.png'))
	# Offline Plotly plot
	df_test = pd.read_csv(os.path.join(modelDir, 'Revised Meter Voltage Files', inputDict['checkMeter']))
	min_max_scaler = preprocessing.MinMaxScaler()
	selectedPhase = 'V_A'
	for phase in ['V_A','V_B','V_C']:
		df_test[[phase]] = min_max_scaler.fit_transform(df_test[[phase]])
		# Check for non-zero data.
		if max(df_test[[phase]]) > 0.0:
			selectedPhase = phase
	y0 = df_ss['V_A']
	y1 = df_ss['V_B']
	y2 = df_ss['V_C']
	y3 = df_test[selectedPhase]
	new_x = range(len(y0))
	# Create traces
	trace0 = go.Scatter(
		x = new_x,
		y = y0,
		# xaxis='x4',
		# yaxis='y1',
		mode = 'lines',
		name = 'SS_PH_A'
	)
	trace1 = go.Scatter(
		x = new_x,
		y = y1,
		# xaxis='x4',
		# yaxis='y2',
		mode = 'lines',
		name = 'SS_PH_B'
	)
	trace2 = go.Scatter(
		x = new_x,
		y = y2,
		# xaxis='x4',
		# yaxis='y3',
		mode = 'lines',
		name = 'SS_PH_C'
	)
	trace3 = go.Scatter(
		x = new_x,
		y = y3,
		# xaxis='x4',
		# yaxis='y4',
		mode = 'lines',
		name = inputDict['checkMeter'] + ' ' + selectedPhase
	)
	data = [trace0, trace1, trace2, trace3]
	# Create layout
	meterDetailLayout = go.Layout(
		width=1000,
		height=500,
		xaxis=dict(
			showgrid=False,
			title="Time Step"
		),
		yaxis=dict(
			title="Volts (PU)",
		),
		legend=dict(
			x=0,
			y=1.1,
			orientation="h"
		),
		margin=go.layout.Margin(
			l=60,
			r=20,
			b=70,
			t=0,
			pad=4
	    ),
	)
	# fig = tools.make_subplots(rows=4, cols=1, subplot_titles=('SS','SSS','SSSS','SSSSSS'))
	# fig.append_trace(trace0, 1, 1)
	# fig.append_trace(trace1, 2, 1)
	# fig.append_trace(trace2, 3, 1)
	# fig.append_trace(trace3, 4, 1)
	# fig['layout'].update(height=800, width=1000, showlegend=False)
	# meterDetailLayout = fig['layout']
	# For non-jupyter plotting.
	plotly.offline.plot(data, filename=pJoin(modelDir, 'output-chart.html'), auto_open=False)
	# Clean up temp files (optional)
	shutil.rmtree(pJoin(modelDir, METER_DIR), ignore_errors=True)
	shutil.rmtree(pJoin(modelDir, 'Revised Meter Voltage Files'), ignore_errors=True)
	shutil.rmtree(pJoin(modelDir, 'Revised Substation Voltage Files'), ignore_errors=True)
	# write our outData
	with open(pJoin(modelDir,"output-conf-matrix.png"),"rb") as inFile:
		outData["confusionMatrixImg"] = inFile.read().encode("base64")
	with open(pJoin(modelDir,"output-regression-result.csv"), "r") as inFile:
		outData["regressionResult"] = list(csv.reader(inFile))
	outData["meterDetailData"] = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
	outData["meterDetailLayout"] = json.dumps(meterDetailLayout, cls=plotly.utils.PlotlyJSONEncoder)
	return outData

def new(modelDir):
	""" Create a new instance of this model. Returns true on success, false on failure. """
	defaultInputs = {
		"user": "admin",
		"subMeterData": open(
			pJoin(
				__neoMetaModel__._omfDir,
				"static",
				"testFiles",
				"rec_sub_meter.csv",
			)
		).read(),
		"subMeterFileName": "rec_sub_meter.csv",
		"meterZip": b64encode(
			open(
				pJoin(
					__neoMetaModel__._omfDir,
					"static",
					"testFiles",
					"meters_transformed.zip"
				)
			).read()
		),
		"meterZipName": "meters_transformed.zip",
		"checkMeter": 'Meter_13.csv',
		"modelType": modelName
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	return creationCode

def _simpleTest():
	# Location
	modelLoc = pJoin(
		__neoMetaModel__._omfDir,
		"data",
		"Model",
		"admin",
		"Automated Testing of " + modelName,
	)
	# Blow away old test results if necessary.
	shutil.rmtree(modelLoc, ignore_errors=True)
	# Create New.
	new(modelLoc)
	# Pre-run.
	# renderAndShow(modelLoc)
	# Run the model.
	runForeground(modelLoc)
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == "__main__":
	_simpleTest()

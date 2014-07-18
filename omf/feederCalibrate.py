'''
Take in a Feeder and an appropriate set of SCADA data, and return the feeder with load shape models attached.

python -c "import populateFeeder; newTree, key = feederCalibrate.startCalibration(working_directory, feederTree, scadaInfo, fileName, feederConfig=None):"

@author: Andrew Fisher
'''

import datetime
import os
import glob
import re
import subprocess
import math
import tempfile
import feederPopulate
import feeder

# Set flag to save 'losing' files as opposed to deleting them during cleanUP() (0 = delete, 1 = save)
savelosers = 0
winning_calibration_IDs = []
# Set WSM score under which we'll kick out the simultion as "close enough" (0.0500, might be an Ok value)
wsm_acceptable = 0.00500
# The weighted priorities assigned to each metric to produce the overall WSM score.
def _calcPriorities ():
	'''Calculate weights for each "difference metric" based on pairwise comparisons defined earlier.
	Return wieghts for peak value, peak time, total energy, minimum value, minimum time.
	Return wieghts for summer, winter, and shoulder.
	'''
	pv_r = 21;
	pt_r = 1.0/3.0 + 14;
	te_r = 1.0/3.0 + 1.0/2.0 + 9;
	mv_r = 1.0/5.0 + 1.0/4.0 + 1.0/2.0 + 3;
	mt_r = 1.0/7.0 + 1.0/6.0 + 1.0/4.0	+ 1.0/2.0 	+ 1;
	total = pv_r + pt_r + te_r + mv_r + mt_r;
	pv = pv_r/total;
	pt = pt_r/total;
	te = te_r/total;
	mv = mv_r/total;
	mt = mt_r/total;	
	S_r = 14;
	W_r = 1.0/4.0 + 9;
	s_r = 1.0/9.0 + 1.0/8.0 + 1;
	tota1 = S_r + W_r + s_r;
	su = S_r/tota1;
	wi = W_r/tota1;
	sh = s_r/tota1;
	return pv, pt, te, mv, mt, su, wi, sh;

def _calcGlobalPriorities (p):
	'''Further weight the calculated priorities of each "difference metric" by the season priorities. '''
	summer = [];
	winter = [];
	shoulder = [];
	for i in xrange (len(p[0:5])):
		summer.append(p[0:5][i] * p[5]);
		winter.append(p[0:5][i] * p[6]);
		shoulder.append(p[0:5][i] * p[7]);
	return summer, winter, shoulder;

weights = _calcGlobalPriorities(_calcPriorities());
# Record of.glm ID, WSM score, and failure or success to improve calibration, all indexed by calibration round number
calib_record = {}
# Dictionary tracking number of times an action is attempted. (action_count[action] = no. attempts)
action_count = {}
# Dictionary tracking number of times an action fails to improve calibration. This is wiped whenever a brand new action is attempted. 
action_failed_count = {}
# The number of times an action may produce a unhelpful result before we begin bypassing it. Once a brand new action is attempted, fail counts are wiped and the action may be tried again. 
fail_lim = 1
# The default parameters. NOTE: These should match the defaults within Configuration.py.
default_params = [15000,35000,0,2,2,0,0,0,0,2700,.15,0]
# log = open('calibration_log.csv','a')
# log.write('-- Begin Calibration Log --\n')
# log.write('ID,\tWSM,\tActionID,\tWSMeval,\tAvg. House,Avg. Comm.,Base Load Scalar,Cooling Offset,Heating Offset,COP high scalar,COP low scalar, Res. Sched. Skew, Decrease Gas Heat, Sched. Skew. Std. Dev., Window Wall Ratio, Additional Heat Degrees, Load Shape Scalar,Summer Peak, Summer Total Energy, Winter Peak, Winter Total Energy\n')

def _convert(d):
	'''Takes list of 4 numbers and returns coded list based on higher, equal, less than 0.'''
	[ps,es,pw,ew] = d;
	v = [0,0,0,0];
	if ps < 0:
		v[0]=1;
	elif ps == 0:
		v[0]=2;
	elif ps > 0:
		v[0]=3;
	if es < 0:
		v[1]=1;
	elif es == 0:
		v[1]=2;
	elif es > 0:
		v[1]=3;
	if pw < 0:
		v[2]=1;
	elif pw == 0:
		v[2]=2;
	elif pw > 0:
		v[2]=3;
	if ew < 0:
		v[3]=1;
	elif ew == 0:
		v[3]=2;
	elif ew > 0:
		v[3]=3;
	return v;
	
def _chooseAction(difs):
	'''Using 4 main metrics, decide which action to take.'''
	actionDict = {  1:[ 'raise load',[1,1,1,1],[2,1,1,1],[2,1,2,1]],
		-1: ['lower load',[3,3,3,3],[2,3,3,3],[2,3,2,3]],
		 2: ['raise winter load',[3,3,1,1],[3,2,1,1],[2,3,1,1],[2,2,1,1],[2,3,2,1],[2,2,2,1]],
		-2: ['lower winter load',[1,1,3,3],[1,2,3,3],[2,1,3,3],[2,2,3,3],[2,1,2,3],[2,2,2,3]],
		 3: ['raise winter peak',[3,3,1,3],[2,3,1,3],[2,2,1,3],[2,2,1,2],[2,3,1,2],[3,3,1,2]],
		-3: ['lower winter peak',[1,1,3,1],[2,1,3,1],[2,2,3,1],[2,2,3,2],[2,1,3,2],[1,1,3,2]],
		 4: ['raise winter & summer',[1,1,1,3],[2,1,1,3],[2,1,1,2],[1,1,1,2]],
		-4: ['lower winter & summer',[3,3,3,1],[2,3,3,1],[2,3,3,2],[3,3,3,2]],
		 5: ['raise summer load',[1,3,3,3],[1,3,2,3],[1,3,2,2],[1,2,2,3],[1,2,2,2],[1,1,2,2],[1,1,2,3],[2,1,2,2]],
		-5: ['lower summer load',[3,1,1,1],[3,1,2,1],[3,1,2,2],[3,2,2,1],[3,2,2,2],[3,3,2,2],[3,3,2,1],[2,3,2,2]],
		 6: ['raise summer & winter',[1,3,1,1],[1,3,2,1],[1,1,2,1],[1,2,2,1]],
		-6: ['lower summer & winter',[3,1,3,3],[3,1,2,3],[3,3,2,3],[3,1,1,3]],
		 7: ['raise peaks',[1,3,1,3],[1,3,1,2],[1,2,1,2],[1,2,1,3],[1,2,1,1]],
		-7: ['lower peaks',[3,1,3,1],[3,1,3,2],[3,2,3,2],[3,2,3,1],[3,2,3,3]],
		 8: ['raise summer & lower winter',[1,3,3,1],[1,2,3,1],[1,2,3,2],[1,3,3,2]],
		-8: ['lower summer & raise winter',[3,1,1,3],[3,1,1,2],[3,2,1,3],[3,2,1,2]] };
	checkVal = _convert(difs);
	if  0 in checkVal:
		print ("Ooops! Something is the matter.");
		return;
	else:
		for i in actionDict.keys():
			if checkVal in actionDict[i]:
				return i, actionDict[i][0];

def _getValues(vdir,glm_filenames,days):
	''' Take list of all .glms that were ran and return measurements for each metric.
	vdir -- path to the working directory
	glm_filenames -- List of filenames for every .glm that was ran in GridLab-D 
	days -- List of dates for summer, winter, and spring. Should match the dates referenced in the .glm filenames
	This function also evaluates by querying the MySQL database whether a .glm ran successfully or not. If it was not successful, it is discounted.
	'''
	measurements = {}
	orig_len = len(glm_filenames)
	for i in glm_filenames:
		print ("Attempting to gather measurements from "+i)
		# Check that each feeder version has records for three days, and that each ran .glm has a complete (or nearly complete) record set (96 entries). 
		c = 0
		filename = os.path.join(vdir, 'csv_output', re.sub('\.glm$','_network_node_recorder.csv',i))
		if not os.path.isfile(filename):
			print ("	Missing simulation output for "+i)
			continue
		else:
			csv = open (filename, 'r')
			lines = csv.readlines()
			for l in lines:
				if l.startswith("#"):
					continue
				else:
					c += 1
			if c < 96:
				csv.close()
				print ("	Missing simulation output for "+i+". "+str(c)+"/96 five-minute intervals were recorded.")
				continue
		# Get annual .glm ID by stripping the date from the filename. 
		m = re.match(r'^Calib_ID(\d*)_Config_ID(\d*)',i)
		if m is not None:
			glm_ID = m.group()
		else:
			m = re.match(r'^DefaultCalibration',i)
			if m is not None:
				glm_ID = m.group()
			else:
				print ("	Can't recognize file name: "+str(i)+". Going to ignore it.")
				continue
		if glm_ID not in measurements.keys():
			measurements[glm_ID] = [ [None], [None], [None] ]
		# Determine what season this .glm was for.
		season = None
		for j in xrange(len(days)):
			if re.match(r'^.*'+days[j]+'.*$',i) is not None:
				season = j
		if season is None:
			print ("File "+str(i)+" isn't matching any of "+str(days)+".")
			measurements[glm_ID] = None
		else:
			pv = 0.0
			mv = 1e15
			te = 0.0
			for l in lines:
				if l.startswith("#"):
					continue
				else:
					vals = l.split(',')
					if pv < float(vals[1]):
						pv = float(vals[1])
						pt_stamp = re.sub('\s\w{3}','',vals[0])
					if mv > float(vals[1]):
						mv = float(vals[1])
						mt_stamp = re.sub('\s\w{3}','',vals[0])
					if te < float(vals[2]):
						te = float(vals[2])
			csv.close()
			pt_date = datetime.datetime.strptime(pt_stamp,'%Y-%m-%d %H:%M:%S')
			mt_date = datetime.datetime.strptime(mt_stamp,'%Y-%m-%d %H:%M:%S')
			pt = float(pt_date.hour)
			mt = float(mt_date.hour)
			pv = pv/1000.0
			te = te/1000.0
			mv = mv/1000.0
			measurements[glm_ID][season] = [pv,pt,te,mv,mt]
	# Make sure we only continue evaluation with glms that have all three days completely recorded. 
	topop=[]
	for j in measurements.keys():
		if measurements[j] is None: 
			topop.append(j)
		else:
			for k in measurements[j]:
				if k[0] is None: 
					topop.append(j)
	if len(topop) != 0:
		for i in topop:
			if i in measurements.keys():
				print ("Ignoring "+i+" due to missing simulation output.")
				measurements.pop(i)
	print (str(len(measurements))+" of "+ str(orig_len/3)+ " calibrated models successfully ran.")
	return measurements
	

def _calcDiffs (glm_vals, scada):
	'''Calculate percent differences for [peak val, peak time, total energy, minimum val, minimum time] from recorder output from simulation of given glm on given day.'''
	diffs = [];
	for i in xrange(len(glm_vals)):
		if i == 1 or i == 4: # time of peak or time of minimum
			j = round((glm_vals[i] - scada[i])/24.0,4);
		elif scada[i] == 0.0 or glm_vals[i] == 0.0:
			if glm_vals[i] != scada[i]:
				j = (glm_vals[i] - scada[i])/abs(glm_vals[i] - scada[i])
			else:
				j = 0.0  
		else:
			j = round((glm_vals[i] - scada[i])/scada[i],4);
		diffs.append(j);
	return diffs;

# We'll need to calculate the 5 metrics for each season for each comparison run. 
def _funcRawMetsDict (wdir, glms,scada,days):
	'''Create dictionary of metrics for each .glm in question
	wdir -- Path to the working directory
	glms -- A list of file names of .glms to compare
	scada -- The SCADA values to be compared with .glm simulation output
	days -- The list of dates for summer, winter, shoulder
	'''
	# Create dictionary with measurements for each successfuly ran *.glm.
	# Note: "Successfully ran" means that each of the three days ran successfully for a certain calibration.
	measurements = _getValues(wdir, glms,days)
	raw_metrics = {};
	for i in measurements.keys():
		# Set up an entry in the raw metrics dictionary for each calibrated *.glm.
		raw_metrics[i] = [];
	for j in raw_metrics.keys():
		raw_metrics[j].append(_calcDiffs(measurements[j][0],scada[0]));
		raw_metrics[j].append(_calcDiffs(measurements[j][1],scada[1]));
		raw_metrics[j].append(_calcDiffs(measurements[j][2],scada[2]));
	return raw_metrics

def _applyWeights (w,su,wi,sh):
	'''Apply global priorities of each metric to measured differences & return WSM score.'''
	score = 0;
	c = 0;
	for j in [su,wi,sh]:
		for i in xrange (len(j)):
			score = score + (w[c][i]*abs(j[i]));
		c = c + 1;
	return score;

def _chooseBest (mets):
	'''Return "best" .glm by finding .glm with smallest WSM score.'''
	w = {};
	k = [];
	for i in mets.keys():
		# Create list of keys.
		k.append(i);
		# Create dictionary linking .glm with WSM score.
		w[i] = _applyWeights(weights,mets[i][0],mets[i][1],mets[i][2]);
	# Find smallest WSM score.
	if w:
		m = k[0];
		l = w[m];
		for i in w.keys():
			if w[i] < l:
				l = w[i];
				m = i;
		# return .glm, score
		return m, l;
		
def _warnOutliers(metrics):
	'''Print warnings for outlier metrics.'''
	# metrics is in form [peak val, peak time, total energy, minimum val, minimum time] for summer = 0, winter = 1, shoulder = 2
	season_titles = ['Summer', 'Winter', 'Spring']
	metric_titles = ['Peak Value', 'Peak Time', 'Total Energy', 'Min. Value', 'Min. Time']
	for seasonID in xrange(3):
		print ("\n")
		for metricID in xrange(5):
				print (season_titles[seasonID] +" "+metric_titles[metricID]+":\t"+str(round(100 * metrics[seasonID][metricID],2))+"% difference.")
			
def _getMainMetrics (glm, raw_metrics):
	'''Get main four metrics for a given .glm.
	The percent differences between SCADA and simulated for:
	Summer Peak Value, Summer Total Energy, Winter Peak Value, Winter Total Energy.
	'''
	pv_s = raw_metrics[glm][0][0];
	pv_w = raw_metrics[glm][1][0];
	te_s = raw_metrics[glm][0][2];
	te_w = raw_metrics[glm][1][2];
	return [pv_s,te_s,pv_w,te_w];

def _num(s):
	'''Convert a value into an integer or float.'''
	try:
		return int(s)
	except ValueError:
		try:
			return float(s)
		except ValueError:
			return None
	
def _writeLIB (cl_id, calib_id, config_dict, load_shape_scalar):
	'''create a calibration dictionary
	cl_id (int)-- ID of calibration file within this loop
	calib_id (int)-- ID of calibration loop within _calibrateFeeder function
	params (list)-- list of calibration values for populating .glm
	wdir (string)-- the directory in which these files should be written
	config_dict
	load_shape_scalar (float)-- if using case flag = -1 (load shape rather than houses)
	'''
	from copy import deepcopy
	if config_dict != None:
		calibration_config = deepcopy(config_dict)
		calibration_config['ID'] = 'Calib_ID'+str(calib_id)+'_Config_ID'+str(cl_id)
		calibration_config['load_shape_scalar'] = load_shape_scalar
	else:
		calibration_config = {'ID' : 'Calib_ID'+str(calib_id)+'_Config_ID'+str(cl_id),
											'load_shape_scalar' : load_shape_scalar}
		
	return calibration_config

def _cleanUP(cleandir):
	'''Delete all .glm files in preparation for the next calibration round.'''
	for files in os.listdir(cleandir):
		del_file = os.path.join(cleandir, files)
		try:
			if os.path.isfile(del_file):
				os.remove(del_file)
		except:
			print('could not delete {:s}'.format(files))

def _bestSoFar(counter):
	'''finds smallest WSM score recorded so far'''
	c = calib_record[counter][1]
	n = counter
	for i in calib_record.keys():
		if calib_record[i][1] < c:
			c = calib_record[i][1]
			n = i
	return n, c
	
def _WSMevaluate(wsm_score_best, counter):
	'''Evaluate current WSM score and determine whether to stop calibrating.'''
	# find smallest WSM score recorded
	c = calib_record[counter-1][1]
	for i in calib_record.keys():
		if i == counter:
			continue
		else:
			if calib_record[i][1] < c:
				c = calib_record[i][1]
	if wsm_score_best < wsm_acceptable:
		return 1
	elif wsm_score_best >= c: #WSM score worse than last run. Try second choice action.
		return 2
	else: # WSM better but still not acceptable. Loop may continue.
		return 0

def _clockDates(days):
	''' Creates a dictionary of start and stop timestamps for each of the three dates being evaluated '''
	clockdates = {}
	for i in days:
		j = datetime.datetime.strptime(i,'%Y-%m-%d')
		start_time = (j - datetime.timedelta(days = 1)).strftime('%Y-%m-%d %H:%M:%S')
		rec_start_time = j.strftime('%Y-%m-%d %H:%M:%S')
		stop_time = (j - datetime.timedelta(days = -1)).strftime('%Y-%m-%d %H:%M:%S')
		clockdates[rec_start_time] = (start_time,stop_time)
	return clockdates

def _movetoWinners(glm_ID,windir):
	'''Move the .glms associated with the round's best calibration to a subdirectory and move the associated calibration configuration to the winning configuration list'''
	# assuming glm_ID is 'Calib_IDX_Config_IDY', get the three .glms associated with this run. 
	try:
		os.mkdir(os.path.join(windir, 'winners'))
	except:
		pass
	for filename in glob.glob(os.path.join(windir, glm_ID + '*.glm')):
		os.rename(filename, os.path.join(windir, "winners", os.path.basename(filename)))
	
def _failedLim(action):
	''' Check if an action has reached it's 'fail limit'. '''
	if action in action_failed_count.keys():
		if action_failed_count[action] >= fail_lim:
			print ("\tOoops, action id "+str(action)+" has met its fail count limit for now. Try something else.")
			return 1
		else:
			return 0
	else:
		return 0

def _takeNext(desired,last):
	next_choice_actions = {1 : { 1 : 7, 7 : 2, 2 : 5, 5 : 3, 3 : 4, 4 : 6, 6 : 8, 8 : 0 },
										2 : { 2 : 3, 3 : 4, 4 : 1 , 1 : 7, 7 : 0 },
										3 : { 3 : 2, 2 : 4, 4 : 7, 7 : 1, 1 : 0 },
										4 : { 4 : 3, 3 : 7, 7 : 8, 8 : 1, 1 : 0 },
										5 : { 5 : 6, 6 : 7, 7 : 1, 1 : 0 },
										6 : { 6 : 7, 7 : 5, 5 : 6, 6 : 1, 1 : 0 },
										7 : { 7 : 1, 1 : 4, 4 : 3, 3 : 2, 2 : 5, 5 : 0 },
										8 : { 8 : 3, 3 : 2, 2 : 5, 5 : 0 }}
	nextnum = (desired/abs(desired)) * (next_choice_actions[abs(desired)][abs(last)])
	if not _failedLim(nextnum):
		return nextnum
	else:
		return _takeNext(desired,nextnum)
	
def _calibrateLoop(glm_name, main_mets, scada, days, eval_int, counter, baseGLM, case_flag, feeder_config, cal_dir):
	'''This recursive function loops the calibration process until complete.
	Arguments:
	glm_name -- ID of "best" .glm so far (CalibX_Config_Y) 
	main_mets (list)-- Summer Peak Value diff, Summer Total Energy diff, Winter Peak Value diff ,Winter Total Energy diff for glm_name. Used to determine action.
	scada (list of lists)-- SCADA values for comparing closeness to .glm simulation output.
	days (list)-- list of dates for summer, winter, and spring
	eval_int (int)-- result of evaluating WSM score against acceptable WSM and previous WSM. 0 = continue with first choice action, 2 = try "next choice" action
	counter (int)-- Advances each time this function is called.
	baseGLM (dictionary)-- orignal base dictionary for use in feederPopulate.py
	case_flag (int)-- also for use in feederPopulate.py
	feeder_config (string)-- (string TODO: this is future work, leave as 'None')-- feeder configuration file (weather, sizing, etc)
	cal_dir (string)-- directory where files for this feeder are being stored and ran
	batch_file (string)-- filename of the batch file that was created to run .glms in directory
	Given the above input, this function takes the following steps:
	1. Advance counter.
	2. Use main metrics to determine which action will further calibrate the feeder model. 
	3. Create a calibration file for each set of possible calibration values.
	4. For each calibration file that was generated, create three .glms (one for each day).
	5. Run all the .glm models in GridLab-D.
	6. For each simulation, compare output to SCADA values. 
	7. Calculate the WSM score for each .glm.
	8. Determine which .glm produced the best WSM score. 
	9. Evaluate whether or not this WSM score indicates calibration must finish.
	10. If finished, return the final .glm. If not finished, send "best" .glm, its main metrics, the SCADA values, and the current counter back to this function. 
	'''
	action_desc ={	 1: 'raise load',
								-1: 'lower load',
								 2: 'raise winter load',
								-2: 'lower winter load',
								 3: 'raise winter peak',
								-3: 'lower winter peak',
								 4: 'raise winter & summer',
								-4: 'lower winter & summer',
								 5: 'raise summer load',
								-5: 'lower summer load',
								 6: 'raise summer & winter',
								-6: 'lower summer & winter',
								 7: 'raise peaks',
								-7: 'lower peaks',
								 8: 'raise summer & lower winter',
								-8: 'lower summer & raise winter',
								 0: 'stop calibration',
								-0: 'stop calibration' };
	# Advance counter. 
	counter += 1
	print ('\n****************************** Calibration Round # '+str(counter)+':')
	# Get the last action
	last_action = calib_record[counter-1][2]
	failed = calib_record[counter-1][3]
	print ("The last action ID was "+str(last_action)+". (Fail code = "+str(failed)+")")
	if last_action == 9:
		# we want last action tried before a schedule skew test round
		last_action = calib_record[counter-2][2]
		failed = calib_record[counter-2][3]
		print ("We're going to consider the action before the schedule skew test, which was "+ str(last_action)+". (Fail code = "+str(failed)+")")
	# Delete all .glms from the directory. The winning ones from last round should have already been moved to a subdirectory. 
	# The batch file runs everything /*.glm/ in the directory, so these unnecessary ones have got to go. 
	print ("Removing .glm files from the last calibration round...")
	_cleanUP(cal_dir)
	_cleanUP(os.path.join(cal_dir, 'csv_output'))
	if case_flag == -1:
		action = -1
		desc = 'scale normalized load shape'
		print ("\nBegin choosing calibration action...")
		# Based on the main metrics (pv_s,te_s,pv_w,te_w), choose the desired action.
		desired, desc = _chooseAction(main_mets)
		action = desired
		print ("\tFirst choice: Action ID "+str(action)+" ("+desc+").")
		# Use the 'big knobs' as long as total energy differences are 'really big' (get into ballpark)
		c = 0
		print ("\tAre we in ballpark yet?...")
		if abs(main_mets[1]) > 0.25 or abs(main_mets[3]) > 0.25:
			print ("\tSummer total energy difference is "+str(round(main_mets[1]*100,2))+"% and winter total energy is "+str(round(main_mets[3]*100,2))+"%...")
			c = 1
		else:
			print ("\tYes, summer total energy difference is "+str(round(main_mets[1]*100,2))+"% and winter total energy is "+str(round(main_mets[3]*100,2))+"%.")
		if c == 1:
			if main_mets[1] < 0 and main_mets[3] < 0: # summer & winter low
				print ("\tTrying to raise load overall (Action ID 1 or 7)...")
				if not _failedLim(1):
					action = 1
				elif not _failedLim(7):
					action = 7
			elif main_mets[1] > 0 and main_mets[3] > 0: # summer & winter high
				print ("\tTrying to lower load overall (Action ID -1 or -7)...")
				if not _failedLim(-1):
					action = -1
				elif not _failedLim(-7):
					action = -7
			elif abs(main_mets[1]) > abs(main_mets[3]):
				if main_mets[1] > 0:
					print ("\tTry to lower load overall (Action ID -1 or -7)...")
					if not _failedLim(-1):
						action = -1
					elif not _failedLim(-7):
						action = -7
				else:
					print ("\tTry to raise load overall (Action ID 1 or 7)...")
					if not _failedLim(1):
						action = 1
					elif not _failedLim(7):
						action = 7
			elif abs(main_mets[3]) > abs(main_mets[1]):
				if main_mets[3] > 0:
					print ("\tTry to lower load overall, or lower winter only (Action ID -1, -7, -2, -3)...")
					if not _failedLim(-1):
						action = -1
					elif not _failedLim(-7):
						action = -7
					elif not _failedLim(-2):
						action = -2
					elif not _failedLim(-3):
						action = -3
				else:
					print ("\tTry to raise load overall, or raise winter only (Action ID 1, 7, 2, 3)...")
					if not _failedLim(1):
						action = 1
					elif not _failedLim(7):
						action = 7
					elif not _failedLim(2):
						action = 2
					elif not _failedLim(3):
						action = 3
			desc = action_desc[action]
			print ("\tSet Action ID to "+str(action)+" ( "+desc+" ).")
		if action == desired:
			print ("\tOk, let's go with first choice Action ID "+str(desired))
		if _failedLim(action):
			# reached fail limit, take next choice
			action = _takeNext(action,action)
			desc = action_desc[action]
			print ("\tTrying action "+str(action)+" ("+desc+")")
			if abs(action) == 0:
				print ("\tWe're all out of calibration options...")
				_cleanUP(cal_dir)
				_cleanUP(os.path.join(cal_dir, 'csv_output'))
				return glm_name
		# Once every few rounds, make sure we check some schedule skew options
		if counter in [3,7,11,15] and not _failedLim(9):
			action, desc = 9, "test several residential schedule skew options"
	# Update action counters
	if action in action_count.keys():
		action_count[action] += 1
	else:
		action_count[action] = 1
	print ("\tFINAL DECISION: We're going to use Action ID "+str(action)+" ( "+desc+" ). \n\tThis action will have been tried " + str(action_count[action]) + " times.")
	c = 0;
	calibration_config_files = []
	if case_flag == -1:
		# Scaling normalized load shape
		last_scalar = feeder_config['load_shape_scalar']
		avg_peak_diff = (main_mets[0] + main_mets[2])/2
		ideal_scalar = round(last_scalar * (1/(avg_peak_diff + 1)),4)
		a = round(last_scalar + (ideal_scalar - last_scalar) * 0.25,4)
		b = round(last_scalar + (ideal_scalar - last_scalar) * 0.50,4)
		d = round(last_scalar + (ideal_scalar - last_scalar) * 0.75,4)
		load_shape_scalars = [a, b, d, ideal_scalar]
		for i in load_shape_scalars:
			calibration_config_files.append(_writeLIB(c, counter, feeder_config, i))
			c += 1
	# Populate feeder .glms for each file listed in calibration_config_files
	glms_ran = []
	for i in calibration_config_files:
		# need everything necessary to run feederPopulate.py
		glms_ran.extend(_makeGLM(_clockDates(days), i, baseGLM, case_flag, cal_dir))
	# Run all the .glms:
	raw_metrics = _runGLMS(cal_dir, scada, days)
	if len(raw_metrics) == 0:
		if case_flag == -1:
			print ("All runs failed.")
			return glm_name
	else:
		# Choose the glm with the best WSM score.
		glm_best, wsm_score_best = _chooseBest(raw_metrics)
		print ('** The winning WSM score this round is ' + str(wsm_score_best) + '.')
		print ('** Last round\'s WSM score was '+str(calib_record[counter-1][1])+'.')
		# Evaluate WSM scroe
		wsm_eval = _WSMevaluate(wsm_score_best, counter)
		# Update calibration record dictionary for this round.
		calib_record[counter] = [glm_best,wsm_score_best,action,wsm_eval]
		Roundbestsofar,WSMbestsofar = _bestSoFar(counter)
		print ('** Score to beat is '+str(WSMbestsofar)+' from round '+str(Roundbestsofar)+'.')
		# Print warnings about any outlier metrics. 
		_warnOutliers(raw_metrics[glm_best])
		if wsm_eval == 1: 
			print ("This WSM score has been deemed acceptable.")
			_movetoWinners(glm_best,cal_dir)
			m = re.match(r'^Calib_ID(\d*)_Config_ID(\d*)',glm_best)
			for calib in calibration_config_files:
				if 'ID' in calib.keys() and m.group() in calib['ID']:
					winning_calibration_IDs.append(calib)
			_cleanUP(cal_dir)
			_cleanUP(os.path.join(cal_dir, 'csv_output'))
			return glm_best
		else:
			# Not looping load scaling, assuming that our second time through will be OK. 
			if case_flag == -1:
				_movetoWinners(glm_best,cal_dir)
				m = re.match(r'^Calib_ID(\d*)_Config_ID(\d*)',glm_best)
				for calib in calibration_config_files:
					if 'ID' in calib.keys() and m.group() in calib['ID']:
						winning_calibration_IDs.append(calib)
				_cleanUP(cal_dir)
				_cleanUP(os.path.join(cal_dir, 'csv_output'))
				return glm_best
				
def _makeGLM(clock, calib_file, baseGLM, case_flag, mdir):
	'''Create populated dict and write it to .glm file
	- clock (dictionary) links the three seasonal dates with start and stop timestamps (start simulation full 24 hour before day we're recording)
	- calib_file (dictionary) -- dictionary containing calibration parameters.
	- baseGLM (dictionary) -- orignal base dictionary for use in feederPopulate.py
	- case_flag (int) -- flag technologies to test
	- feeder_config (string TODO: this is future work, leave as 'None')-- feeder configuration file (weather, sizing, etc)
	- mdir(string)-- directory in which to store created .glm files
	'''
	# Create populated dictionary.
	if calib_file is not None:
		calib_obj = calib_file
	else:
		print ('Populating feeder using default calibrations.')
		calib_obj = None
	glmDict, last_key = feederPopulate.startPopulation(baseGLM,case_flag,calib_obj) 
	fnames =  []
	for i in clock.keys():
		# Simulation start
		starttime = clock[i][0]
		# Recording start
		rec_starttime = i
		# Simulation and Recording stop
		stoptime = clock[i][1]
		# Calculate limit.
		j = datetime.datetime.strptime(rec_starttime,'%Y-%m-%d %H:%M:%S')
		k = datetime.datetime.strptime(stoptime,'%Y-%m-%d %H:%M:%S')
		diff = (k - j).total_seconds()
		limit = int(math.ceil(diff / 300.0))
		populated_dict = glmDict
		# Name the file.
		if calib_file is None:
			ident = 'DefaultCalibration'
		else:
			ident= calib_file['ID']
		date = re.sub('\s.*$','',rec_starttime)
		filename = ident + '_' + date + '.glm'
		# Get into clock object and set start and stop timestamp.
		for i in populated_dict.keys():
			if 'clock' in populated_dict[i].keys():
				populated_dict[i]['starttime'] = "'{:s}'".format(starttime)
				populated_dict[i]['stoptime'] = "'{:s}'".format(stoptime)
		lkey = last_key
		# Add GridLAB-D object for recording into *.csv files.
		try:
			os.mkdir(os.path.join(mdir,'csv_output'))
		except:
			pass
		populated_dict[lkey] = {'object' : 'tape.recorder',
									'file' : './csv_output/{:s}_{:s}_network_node_recorder.csv'.format(ident,date),
									'parent' : 'network_node',
									'property' : 'measured_real_power,measured_real_energy',
									'interval' : '{:d}'.format(900),
									'limit' : '{:d}'.format(limit),
									'in': "'{:s}'".format(rec_starttime) }
		# Turn dictionary into a *.glm string and print it to a file in the given directory.
		glmstring = feeder.sortedWrite(populated_dict)
		gfile = open(os.path.join(mdir, filename), 'w')
		gfile.write(glmstring)
		gfile.close()
		print ("\t"+filename+ " is ready.")
		fnames.append(filename)
	return fnames

def _runGLMS(fdir, SCADA, days):
		'''Run all the .glm files found in the directory and return the metrics for each run.'''
		print ('Begining simulations in GridLab-D.')
		glmFiles = [x for x in os.listdir(fdir) if x.endswith('.glm')]
# 		for glm in glmFiles:
# 			with open(os.path.join(fdir,'stdout.txt'),'w') as stdout, open(os.path.join(fdir,'stderr.txt'),'w') as stderr, open(os.path.join(fdir,'PID.txt'),'w') as pidFile:
# 				proc = subprocess.Popen(['C:/Projects/GridLAB-D_Builds/gld3.0/VS2005/Win32/Release/gridlabd.exe', glm], cwd=fdir, stdout=stdout, stderr=stderr)
# 				pidFile.write(str(proc.pid))
# 				proc.wait()
# 		with open(os.path.join(fdir,'stdout.txt'),'w') as stdout, open(os.path.join(fdir,'stderr.txt'),'w') as stderr, open(os.path.join(fdir,'PID.txt'),'w') as pidFile:
# 			proc = subprocess.Popen(['C:/Projects/GridLAB-D_Builds/gld3.0/VS2005/Win32/Release/gridlabd.exe', '-T', '24', '--job'], cwd=fdir, stdout=stdout, stderr=stderr)
# 			pidFile.write(str(proc.pid))
# 			proc.wait()
		proc = []
		for glm in glmFiles:
			with open(os.path.join(fdir,'stdout.txt'),'w') as stdout, open(os.path.join(fdir,'stderr.txt'),'w') as stderr, open(os.path.join(fdir,'PID.txt'),'w') as pidFile:
				proc.append(subprocess.Popen(['C:/Projects/GridLAB-D_Builds/gld3.0/VS2005/Win32/Release/gridlabd.exe', glm], cwd=fdir, stdout=stdout, stderr=stderr))
#				pidFile.write(str(proc.pid))
		for p in proc:
			p.wait()
		print ('Beginning comparison of intitial simulation output with SCADA.')
		raw_metrics = _funcRawMetsDict(fdir, glmFiles, SCADA, days)
		return raw_metrics

def _calibrateFeeder(baseGLM, days, SCADA, case_flag, calibration_config, fdir):
	'''Run an initial .glm model, then begin calibration loop.
	baseGLM(dictionary) -- Initial .glm dictionary. 
	days(list) -- The three days representing summer, winter and shoulder seasons.
	SCADA(list of lists) -- The SCADA values for comparing closeness of .glm simulation output.
	case_flag(integer) -- The case flag for this population (i.e. 0 = base case, -1 = use normalized load shapes)
	feeder_config(string) -- file containing feeder configuration data (region, ratings, etc)
	calibration_config(string) -- file containing calibration parameter values. Most of the time this is null, but if this feeder has been partially calibrated before, it allows for starting where it previously left off.
	fdir (string)-- directory with full file path that files generated for this feeder calibration process are stored
	Given the inputs above, this function takes the following steps:
	1. Create .glm from baseGLM and run the model in GridLab-D.
	2. Compare simulation output to SCADA and calculate WSM score.
	3. Enter score and .glm name into calib_record dictionary under index 0.
	3. Evaluate whether or not this WSM score indicates calibration must finish.
	4. If finished, send final .glm back to OMFmain. If not, send necessary inputs to the recursive calibrateLoop function.
	'''
	# Do initial run. 
	print ('Beginning initial run for calibration.')
	glms_init = []
	r = 0
	c = 0
	calibration_config_files = []
	print("Begin writing calibration files...")
	for val in [0.25, 0.50, 0.75, 1.0, 1.25, 1.50, 1.75, 2.0]:
		calibration_config_files.append(_writeLIB (c, r, calibration_config, val))
		c += 1
	for i in calibration_config_files:
		glms_init.extend(_makeGLM(_clockDates(days), i, baseGLM, case_flag,fdir))
	raw_metrics = _runGLMS(fdir, SCADA, days)
	if len(raw_metrics) == 0:
		# if we can't even get the initial .glm to run... how will we continue? We need to carefully pick our defaults, for one thing.
		print ('All the .glms in '+str(glms_init)+' failed to run or record complete simulation output in GridLab-D. Please evaluate what the error is before trying to calibrate again.')
		# log.write('*all runs failed to run or record complete simulation output \n')
		calib_record[r] = ['*all runs failed', None, -1, None]
		if case_flag == -1:
			_cleanUP(fdir)
			_cleanUP(os.path.join(fdir, 'csv_output'))
			r += 1
			c = 0;
			calibration_config_files = []
			print("Begin writing calibration files...")
			glms_init = []
			for val in [0.01, 0.02, 0.05, 0.10, 0.15]:
				calibration_config_files.append(_writeLIB (c, r, calibration_config, val))
				c += 1
			for i in calibration_config_files:
				glms_init.extend(_makeGLM(_clockDates(days), i, baseGLM, case_flag, fdir))
			raw_metrics = _runGLMS(fdir, SCADA, days)
			if len(raw_metrics) == 0:
				print ('All the .glms in '+str(glms_init)+' failed to run or record complete simulation output in GridLab-D. Please evaluate what the error is before trying to calibrate again.')
				return None, None, None
		else:
			return None, None, None
	# Find .glm with the best WSM score 
	glm, wsm_score = _chooseBest(raw_metrics)
	print ('The WSM score is ' + str(wsm_score) + '.')
	# Print warnings for outliers in the comparison metrics.
	_warnOutliers(raw_metrics[glm])
	# Update calibration record dictionary with initial run values.
	calib_record[r] = [glm, wsm_score, 0, 0]
	if case_flag == -1:
		calib_record[r][2] = -1
	# Get the values of the four main metrics we'll use for choosing an action.
	main_mets = _getMainMetrics(glm, raw_metrics)
	# Since this .glm technically won its round, we'll move it to winners subdirectory. 
	_movetoWinners(glm,fdir)
	m = re.match(r'^Calib_ID(\d*)_Config_ID(\d*)',glm)
	winning_cal = None
	for calib in calibration_config_files:
		if 'ID' in calib.keys() and m.group() in calib['ID']:
			winning_calibration_IDs.append(calib)
			winning_cal = calib
	if wsm_score <= wsm_acceptable:
		print ("Hooray! We're done.")
		final_glm_file = glm
		_cleanUP(fdir)
		_cleanUP(os.path.join(fdir, 'csv_output'))
	else:
		# Go into loop
		try:
			final_glm_file = _calibrateLoop(glm, main_mets, SCADA, days, 0, r, baseGLM, case_flag,winning_cal, fdir)
		except KeyboardInterrupt:
			last_count = max(calib_record.keys())
			print ("Interuppted at calibration loop number "+str(last_count)+" where the best .glm was "+calib_record[last_count][0]+" with WSM score of "+str(calib_record[last_count][1])+".")
			final_glm_file = calib_record[last_count][0]
			_cleanUP(fdir)
	# log.close()
	# Get calibration file from final_glm_file (filename)
	m = re.match(r'^Calib_ID(\d*)_Config_ID(\d*)',final_glm_file)
	winning_cal = None
	for calib in winning_calibration_IDs:
		if 'ID' in calib.keys() and m.group() in calib['ID']:
			winning_cal = calib
	final_dict, last_key = feederPopulate.startPopulation(baseGLM,case_flag,winning_cal)
	_cleanUP(os.path.join(fdir,'winners'))
	_cleanUP(os.path.join(fdir, 'csv_output'))
	os.removedirs(os.path.join(fdir,'winners'))
	os.removedirs(os.path.join(fdir,'csv_output'))
	return winning_cal, final_dict, last_key

def startCalibration(working_directory, feederTree, scadaInfo, fileName, feederConfig=None):
	'''Calibrate a feeder tree using loadshapes'''
	days = [scadaInfo['summerDay'], scadaInfo['winterDay'], scadaInfo['shoulderDay']]
	SCADA = [  [scadaInfo['summerPeakKW'], scadaInfo['summerPeakHour'], scadaInfo['summerTotalEnergy'], scadaInfo['summerMinimumKW'], scadaInfo['summerMinimumHour']],
                            [scadaInfo['winterPeakKW'], scadaInfo['winterPeakHour'], scadaInfo['winterTotalEnergy'], scadaInfo['winterMinimumKW'], scadaInfo['winterMinimumHour']],
                            [scadaInfo['shoulderPeakKW'], scadaInfo['shoulderPeakHour'], scadaInfo['shoulderTotalEnergy'], scadaInfo['shoulderMinimumKW'], scadaInfo['shoulderMinimumHour']]]
	final_calib_file, final_dict, last_key =_calibrateFeeder(feederTree, days, SCADA, -1, feederConfig, working_directory)
	if final_dict is not None:
		return final_dict, final_calib_file
	else:
		return None, None

def _test():
	''' Calibrates an IEEE 13 test feeder using loadshapes and returns the resulting feeder tree and calibration configuration dictionary.'''
	feederTree = feeder.parse('./uploads/IEEE-13.glm')
	model_name = 'calibrated_model_IEEE13'
	working_directory = tempfile.mkdtemp()
	print "Calibration testing in ", working_directory
	scada = {'summerDay' : '2012-06-29',
		'winterDay' : '2012-01-19',
		'shoulderDay' : '2012-04-10',
		'summerPeakKW' : 5931.56,
		'summerTotalEnergy' : 107380.8,
		'summerPeakHour' : 17,
		'summerMinimumKW' : 2988,
		'summerMinimumHour' : 6,
		'winterPeakKW' : 3646.08,
		'winterTotalEnergy' : 75604.32,
		'winterPeakHour' : 21,
		'winterMinimumKW' : 2469.60,
		'winterMinimumHour' : 1,
		'shoulderPeakKW' : 2518.56 ,
		'shoulderTotalEnergy' : 52316.64,
		'shoulderPeakHour' : 21,
		'shoulderMinimumKW' : 1738.08,
		'shoulderMinimumHour' : 2} 
	calibration_config = {'timezone' : 'CST+6CDT',
		'startdate' : '2012-01-01 0:00:00',
		'stopdate' : '2013-01-01 0:00:00',
		'region' : 6,
		'feeder_rating' : 600,
		'nom_volt' : 15000,
		'voltage_players' : [os.path.abspath('./uploads/VA.player').replace('\\', '/'), os.path.abspath('./uploads/VB.player').replace('\\', '/'), os.path.abspath('./uploads/VC.player').replace('\\', '/')],
		'load_shape_scalar' : 1.0,
		'load_shape_player_file' : os.path.abspath('./uploads/load_shape_player.player').replace('\\', '/'),
		'weather_file' : os.path.abspath('./uploads/SCADA_weather_NC_gld_shifted.csv').replace('\\', '/')}
	calibratedFeederTree, calibrationConfiguration = startCalibration(working_directory, feederTree, scada, model_name, calibration_config)
	assert None != calibratedFeederTree
	assert None != calibrationConfiguration

if __name__ ==  '__main__':
	_test()
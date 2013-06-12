import makeWSM
import gleanMetrics
import chooseAction
import takeAction
import next_choice_action
import datetime
import os
import glob
import re
import run_gridlabd_batch_file
import importlib
import Milsoft_GridLAB_D_Feeder_Generation
import makeGLM

# Set WSM score under which we'll kick out the simultion as "close enough" (0.0500, might be an Ok value)
wsm_acceptable = 0.0500
weights = makeWSM.main()
calib_record = {}
action_count = {}


def applyWeights (w,su,wi,sh):
	'''Apply global priorities of each metric to measured differences & return WSM score.'''
	score = 0;
	c = 0;
	for j in [su,wi,sh]:
		for i in range (len(j)):
			score = score + (w[c][i]*abs(j[i]));
		c = c + 1;
	return score;

def chooseBest (mets):
	'''Return "best" .glm by finding .glm with smallest WSM score.'''
	w = {};
	k = [];
	for i in mets.keys():
		# Create list of keys.
		k.append(i);
		# Create dictionary linking .glm with WSM score.
		w[i] = applyWeights(weights,mets[i][0],mets[i][1],mets[i][2]);
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
		
def warnOutliers(metrics,round_num):
	'''Print warnings for outlier metrics.'''
	# metrics is in form [peak val, peak time, total energy, minimum val, minimum time] for summer = 0, winter = 1, shoulder = 2
	season_titles = ['Summer', 'Winter', 'Spring']
	metric_titles = ['Peak Value', 'Peak Time', 'Total Energy', 'Minimum Value', 'Minimum Time']
	warn = {'50%':[], '20%':[], '10%':[]}
	for seasonID in range(3):
		for metricID in range(5):
			if abs(metrics[seasonID][metricID]) > 0.50:
				warn['50%'].append([season_titles[seasonID],metric_titles[metricID],metrics[seasonID][metricID]])
			elif abs(metrics[seasonID][metricID]) > 0.20:
				warn['20%'].append([season_titles[seasonID],metric_titles[metricID],metrics[seasonID][metricID]])
			elif abs(metrics[seasonID][metricID]) > 0.10:
				warn['10%'].append([season_titles[seasonID],metric_titles[metricID],metrics[seasonID][metricID]])
			else:
				pass
	for i in warn.keys():
		print ("Over "+str(i)+" difference from SCADA:")
		for j in warn[i]:
			diff = round(100 * j[2],2)
			print ("\t"+ str(j[0])+" "+str(j[1])+" with "+str(diff)+"% difference.")
			
def getMainMetrics (glm, raw_metrics):
	'''Get main four metrics for a given .glm.
	
	The percent differences between SCADA and simulated for:
	Summer Peak Value, Summer Total Energy, Winter Peak Value, Winter Total Energy.
	
	'''
	pv_s = raw_metrics[glm][0][0];
	pv_w = raw_metrics[glm][1][0];
	te_s = raw_metrics[glm][0][2];
	te_w = raw_metrics[glm][1][2];
	return [pv_s,te_s,pv_w,te_w];

def getCalibVals (glm,dir):
	# Assuming 'glm' is in form Calib_IDX_Config_IDY.
	file = glm+'.py'
	if os.path.isfile(file):
		calib = importlib.import_module(glm)
		calibration_values = calib.all
	else:
		print ("Appears calibration file does not exist, using default parameter values.")
		calibration_values = [5700,35000,.30,3.5,3.5,.75,.75,3600,.50,2700,.15,1] #TODO: These should be defaults. 
	#return [5700,3500,.30,3.5,3.5,.75,.75,3600,.50,2700,.15,1]
	return calibration_values
	
def writeLIB (id, calib_id, params, dir):
	'''Write a file containing calibration values.
	
	id (int)-- ID of calibration file within this loop
	calib_id (int)-- ID of calibration loop within calibrateFeeder function
	params (list)-- list of calibration values for populating .glm
	dir (string)-- the directory in which these files should be written
	
	'''
	[a,b,c,d,e,f,g,h,i,j,k,l] = list(map(lambda x:str(x),params))
	filename = 'Calib_ID'+str(calib_id)+'_Config_ID'+str(id)+'.py' #write in cwd for now--- TODO: change these to text files which we can open and parse from the feeder directory instead. 
	print ("Writing to " + filename)
	file = open(filename, 'w')
	file.write("# "+ file.name +"\n")
	file.write("all = ["+a+","+b+","+c+","+d+","+e+","+f+","+g+","+h+","+i+","+j+","+k+","+l+"]\n")
	file.write("# Determines how many houses to populate (bigger avg_house = less houses)\navg_house="+a+"\n")
	file.write("# Determines sizing of commercial loads (bigger avg_commercial = less houses)\navg_comm="+b+"\n")
	file.write("# Scale the responsive and unresponsive loads (percentage)\nbase_load_scalar="+c+"\n")
	file.write("# cooling offset\ncooling_offset="+d+"\n")
	file.write("# heating offset\nheating_offset="+e+"\n")
	file.write("# COP high scalar\nCOP_high_scalar="+f+"\n")
	file.write("# COP low scalar\nCOP_low_scalar="+g+"\n")
	file.write("# variable to shift the residential schedule skew (seconds)\nres_skew_shift="+h+"\n")
	file.write("# decrease gas heating percentage\ndecrease_gas = "+i+"\n")
	file.write("# widen schedule skew\nsched_skew_std = "+j+"\n")#TODO: this is actually in TechnologyParameters Right now...
	file.write("# window wall ratio\nwindow_wall_ratio = "+k+"\n")
	file.write("# additional set point degrees\naddtl_heat_degrees = "+l+"\n")
	file.close()
	return filename

def cleanUP(dir):
	'''Delete all .glm files in preparation for the next calibration round.'''
	glms = glob.glob(dir+'\\*.glm')
	for glm in glms:
		# glm includes directory path
		os.remove(glm)
	print (str(len(glms))+" files removed.")

def WSMevaluate(wsm_score_best, counter):
	'''Evaluate current WSM score and determine whether to stop calibrating.'''
	if wsm_score_best < wsm_acceptable:
		return 1
	elif wsm_score_best > calib_record[counter][1]: #WSM score worse than last run, try second choice action
		return 2
	else: # wsm better but still not acceptable. loop may continue
		return 0

def clockDates(days):
	clockdates = {}
	for i in days:
		j = datetime.datetime.strptime(i,'%Y-%m-%d')
		start_time = (j - datetime.timedelta(days = 1)).strftime('%Y-%m-%d %H:%M:%S')
		rec_start_time = j.strftime('%Y-%m-%d %H:%M:%S')
		stop_time = (j - datetime.timedelta(days = -1)).strftime('%Y-%m-%d %H:%M:%S')
		clockdates[rec_start_time] = (start_time,stop_time)
	return clockdates

def movetoWinners(glm_ID,dir):
	'''Move the .glms associated with the best calibration to a subdirectory.'''
	# assuming glm_ID is 'Calib_IDX_Config_IDY', get the three .glms associated with this run. 
	for filename in glob.glob(dir+'\\'+glm_ID+'*.glm'):
		os.rename(filename,dir+"\\winners\\"+os.path.basename(filename))
	
def calibrateLoop(glm_name, main_mets, scada, days, eval, counter, baseGLM, case_flag, feeder_config, dir, batch_file):
	'''This recursive function loops the calibration process until complete.
	
	Arguments:
	glm_name -- ID of "best" .glm so far (CalibX_Config_Y) 
	main_mets (list)-- Summer Peak Value diff, Summer Total Energy diff, Winter Peak Value diff ,Winter Total Energy diff for glm_name. Used to determine action.
	scada (list of lists)-- SCADA values for comparing closeness to .glm simulation output.
	days (list)-- list of dates for summer, winter, and spring
	eval (int)-- result of evaluating WSM score against acceptable WSM and previous WSM. 0 = continue with first choice action, 2 = try "next choice" action
	counter (int)-- Advances each time this function is called.
	baseGLM (dictionary)-- orignal base dictionary for use in Milsoft_GridLAB_D_Feeder_Generation.py
	case_flag (int)-- also for use in Milsoft_GridLAB_D_Feeder_Generation.py
	feeder_config (string)-- (string TODO: this is future work, leave as 'None')-- feeder configuration file (weather, sizing, etc)
	dir (string)-- directory where files for this feeder are being stored and ran
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
	# Get the last action
	last_action = calib_record[counter][2]
	
	# Advance counter. 
	counter += 1
	print ("******************************\nCalibration Round # "+str(counter)+":")
	
	# Delete all .glms from the directory. The winning ones from last round should have already been moved to a subdirectory. 
	# The batch file runs everything /*.glm/ in the directory, so these unecessary ones have got to go. 
	print ("Removing .glm files from the last calibration round...")
	cleanUP(dir)
	
	# Based on the main metrics (pv_s,te_s,pv_w,te_w), choose which action we're going to take.
	action, desc = chooseAction.chooseAction(main_mets)
	
	# Once every few rounds, make sure we test schedule skew.
	if counter in [3,6,9,12]:
		action, desc = 9, "test several residential schedule skew options"
		
	# Finalize which action to take.
	if eval == 2: # take "next choice" action instead of the one from chooseAction.py
		action = (action/abs(action)) * (next_choice_action.next_choice_actions[action][last_action])
		desc = next_choice_action.action_desc[action]
		if action == 0:
			print ("We've reached the end of our options.")
			return glm_name
			
	# Update action counters
	if action in action_count.keys():
		action_count[action] += 1
	else:
		action_count[action] = 1
	print ("We're going to " + desc + ". This action will have been tried " + str(action_count[action]) + " times.")
	
	# Take the decided upon action and produce a list of lists with difference calibration parameters to try
	calibrations = takeAction.takeAction(action,getCalibVals(glm_name,dir),main_mets)
	print ("There will be " + str(len(calibrations)) + " calibrations to test.")
	
	# For each list of calibration values in list calibrations, make a .py file.
	c = 0;
	calibration_config_files = []
	for i in calibrations:
		calibration_config_files.append(writeLIB (c, counter, i, dir))
		c += 1
		
	# Populate feeder .glms for each file listed in calibration_config_files
	glms_ran = []
	for i in calibration_config_files:
		# need everything necessary to run Milsoft_GridLAB_D_Feeder_Generation.py
		glms_ran.extend(makeGLM.makeGLM(clockDates(days), i, baseGLM, case_flag, feeder_config,dir))
		
	# Run all the .glms by executing the batch file.
	print ("Begining simulations in GridLab-D.")
	print ("Batch file error code is ...")
	run_gridlabd_batch_file.run_batch_file(dir,batch_file)
	
	# Get comparison metrics between simulation outputs and SCADA.
	raw_metrics = gleanMetrics.funcRawMetsDict(glms_ran, scada, days)
	
	# Choose the glm with the best WSM score.
	glm_best, wsm_score_best = chooseBest(raw_metrics)
	print ("The best WSM score is " + str(wsm_score_best) + ".")
	
	# Print warnings about any outlier metrics. 
	warnOutliers(raw_metrics[glm_best],counter)
	
	# Get values of our four main metrics. 
	main_mets_glm_best = getMainMetrics(glm_best, raw_metrics)
	
	# Update calibration record dictionary for this round.
	calib_record[counter] = [glm_best,wsm_score_best,action]
	
	# Evaluate WSM scroe
	wsm_eval = WSMevaluate(wsm_score_best, counter)
	if wsm_eval == 1: 
		print ("This WSM score has been deemed acceptable.")
		movetoWinners(glm_best,dir)
		return glm_best
	else:
		if wsm_eval == 2:
			# glm_best is not better than the previous. Run loop again but take "next choice" action. 
			print ("That last action did not improve the WSM score from the last round. Let's try again.")
			return calibrateLoop(glm_name, main_mets, scada, days, wsm_eval, counter, baseGLM, case_flag, feeder_config, dir, batch_file)
			       
		else:
			print ("Time for the next round.")
			movetoWinners(glm_best,dir)
			return calibrateLoop(glm_best, main_mets_glm_best, scada, days, wsm_eval, counter, baseGLM, case_flag, feeder_config,dir, batch_file)

def calibrateFeeder(baseGLM, days, SCADA, case_flag, feeder_config, calibration_config, dir):
	'''Run an initial .glm model, then begin calibration loop.
	
	baseGLM(dictionary) -- Initial .glm dictionary. 
	days(list) -- The three days representing summer, winter and shoulder seasons.
	SCADA(list of lists) -- The SCADA values for comparing closeness of .glm simulation output.
	feeder_config(string) -- file containing feeder configuration data (region, ratings, etc)
	calibration_config(string) -- file containing calibration parameter values. Most of the time this is null, but if this feeder has been partially calibrated before, it allows for starting where it previously left off.
	dir (string)-- directory with full file path that files generated for this feeder calibration process are stored
	
	Given the inputs above, this function takes the following steps:
	1. Create .glm from baseGLM and run the model in GridLab-D.
	2. Compare simulation output to SCADA and calculate WSM score.
	3. Enter score and .glm name into calib_record dictionary under index 0.
	3. Evaluate whether or not this WSM score indicates calibration must finish.
	4. If finished, send final .glm back to OMFmain. If not, send necessary inputs to the recursive calibrateLoop function.
	
	'''
	# Name and create batch file.
	batch_file = dir + '\\calibration_batch_file.bat'
	run_gridlabd_batch_file.create_batch_file(dir,batch_file)
	
	# Do initial run. 
	#glm_init_dict = Milsoft_GridLAB_D_Feeder_Generation.GLD_Feeder(baseGLM,case_flag,calibration_config,feeder_config)
	print ("Beginning initial run for calibration.")
	
	# Make .glm's for each day. 
	#glms_init = makeGLM.makeGLM(clockDates(days), calibration_config, baseGLM, case_flag, feeder_config, dir)
	glms_init = ['DefaultCalibration_2013-04-14.glm','DefaultCalibration_2013-01-04.glm','DefaultCalibration_2013-06-29.glm']
	# Run those .glms by executing a batch file. 
	# print ("Begining simulations in GridLab-D.")
	# print ("Batch file error code is ...")
	# run_gridlabd_batch_file.run_batch_file(dir,batch_file)
	
	# Get comparison metrics from simulation outputs
	print ("Beginning comparison of intitial simulation output with SCADA.")
	raw_metrics = gleanMetrics.funcRawMetsDict(glms_init, SCADA, days)
	
	# Find .glm with the best WSM score (at this point there is only one...)
	glm, wsm_score = chooseBest(raw_metrics)
	print ("The initial WSM score is " + str(wsm_score) + ".")
	
	# Print warnings for outliers in the comparison metrics. 
	warnOutliers(raw_metrics[glm],0)
	
	# Update calibration record dictionary with initial run values.
	calib_record[0] = [glm, wsm_score, 0]
	
	# Get the values of the four main metrics we'll use for choosing an action.
	main_mets = getMainMetrics(glm, raw_metrics)
	
	# Since this .glm technically won its round, we'll move it to winners subdirectory. 
	movetoWinners(glm,dir)
	
	if wsm_score <= wsm_acceptable:
		print ("Hooray! We're done.")
		#return None, glm_init_dict # to OMFmain.py
	else:
		# Go into loop
		try:
			final_glm_file = calibrateLoop(glm, main_mets, SCADA, days, 0, 0, baseGLM, case_flag, feeder_config,dir,batch_file)
		except KeyboardInterrupt:
			last_count = max(calib_record.keys())
			print ("Interuppted at calibration loop number "+str(last_count)+" which where the best .glm was "+calib_record[last_count][0]+" with WSM score of "+calib_record[last_count][1])
			final_glm_file = calib_record[last_count][0]
			
	# Get calibration file from final_glm_file (filename)
	m = re.match(r'^Calib_ID(\d*)_Config_ID(\d*)',final_glm_file)
	if m is not None:
		final_calib_file = m.group()+'.py'
	else:
		m = re.match(r'^DefaultCalibration',final_glm_file)
		if m is not None:
			final_calib_file = m.group()+'.py'
		else:
			print ("Can't pull configuration file name from "+final_glm_file)
			final_calib_file = None
				
	final_dict = Milsoft_GridLAB_D_Feeder_Generation.GLD_Feeder(baseGLM,case_flag,final_calib_file,feeder_config)
	return final_calib_file, final_dict

def main():
	#calibrateFeeder(outGLM, days, SCADA, feeder_config, calibration_config)
	print (calibrateFeeder.__name__)
	print (calibrateFeeder.__doc__)
	print (calibrateLoop.__name__)
	print (calibrateLoop.__doc__)
	#warnOutliers([[0.578,0.243,-0.0027,-0.0437,0.0138],[0.3425,-0.9971,-0.0744,-0.1742,0.0033],[0.1310,-0.1492,0.0864,0.0586,0.0554]],3) #testing values
if __name__ ==  '__main__':
	main();
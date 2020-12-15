''' Run OpenDSS and plot the results for arbitrary circuits. '''

import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import math
import os
import warnings
try:
	import opendssdirect as dss
except:
	warnings.warn('opendssdirect not installed; opendss functionality disabled.')
from omf.solvers.opendss import dssConvert

def runDssCommand(dsscmd):
	from opendssdirect import run_command, Error
	x = run_command(dsscmd)
	latest_error = Error.Description()
	if latest_error != '':
		print('OpenDSS Error:', latest_error)
	return x

def runDSS(dssFilePath, keep_output=True):
	''' Run DSS circuit definition file and set export path. Generates file named coords.csv in directory of input file.
	To avoid generating this file, set the 'keep_output' parameter to False.'''
	# Check for valid .dss file
	assert '.dss' in dssFilePath.lower(), 'The input file must be an OpenDSS circuit definition file.'
	# Get paths because openDss doesn't like relative paths.
	fullPath = os.path.abspath(dssFilePath)
	dssFileLoc = os.path.dirname(fullPath)
	try:
		with open(fullPath):
			pass
	except Exception as ex:
		print('While accessing the file located at %s, the following exception occured: %s'%(dssFileLoc, ex))
	runDssCommand('Clear')
	runDssCommand('Redirect "' + fullPath + '"')
	runDssCommand('Solve')
	# also generate coordinates.
	# TODO?: Get the coords as a separate function (i.e. getCoords() below) and instead return dssFileLoc.
	x = runDssCommand('Export BusCoords "' + dssFileLoc + '/coords.csv"')
	coords = pd.read_csv(dssFileLoc + '/coords.csv', dtype=str, header=None, names=['Element', 'X', 'Y'])
	# TODO: reverse keep_output logic - Should default to cleanliness. Requires addition of 'keep_output=True' to all function calls.
	if not keep_output:
		os.remove(x)
	hyp = []
	for index, row in coords.iterrows():
		hyp.append(math.sqrt(float(row['X'])**2 + float(row['Y'])**2))
	coords['radius'] = hyp
	return coords

def _getCoords(dssFilePath, keep_output=True):
	'''*Not approved for usage*. Takes in an OpenDSS circuit definition file and outputs the bus coordinates as a dataframe. If 
	'keep_output' is set to True, a file named coords.csv is generated in the directory of input file.'''
	# TODO: clean up and test the below copy-pasta'd logic
	#dssFileLoc = runDSS(dssFilePath, keep_output=True)
	dssFileLoc = runDSS(dssFilePath)
	x = runDssCommand('Export BusCoords "' + dssFileLoc + '/coords.csv"')
	coords = pd.read_csv(dssFileLoc + '/coords.csv', header=None)
	if not keep_output:
		os.remove(x)
	coords.columns = ['Element', 'X', 'Y', 'radius'] # most everything renames 'Element' to 'Bus'. currentPlot() and capacityPlot() change it to 'Index' for their own reasons.
	hyp = []
	for index, row in coords.iterrows():
		hyp.append(math.sqrt(row['X']**2 + row['Y']**2))
	coords['radius'] = hyp
	return coords

def newQstsPlot(filePath, stepSizeInMinutes, numberOfSteps, keepAllFiles=False, actions={}):
	''' Use monitor objects to generate voltage values for a timeseries powerflow. '''
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	volt_coord = runDSS(filePath)
	# Attach Monitors
	tree = dssConvert.dssToTree(filePath)
	mon_names = []
	circ_name = 'NONE'
	for ob in tree:
		obData = ob.get('object','NONE.NONE')
		obType, name = obData.split('.')
		mon_name = f'mon{obType}-{name}'
		if obData.startswith('circuit.'):
			circ_name = name
		elif obData.startswith('vsource.'):
			runDssCommand(f'new object=monitor.{mon_name} element={obType}.{name} terminal=1 mode=0')
			mon_names.append(mon_name)
		elif obData.startswith('generator.'):
			runDssCommand(f'new object=monitor.{mon_name} element={obType}.{name} terminal=1 mode=1 ppolar=no')
			mon_names.append(mon_name)
		elif ob.get('object','').startswith('load.'):
			runDssCommand(f'new object=monitor.{mon_name} element={obType}.{name} terminal=1 mode=0')
			mon_names.append(mon_name)
		elif ob.get('object','').startswith('capacitor.'):
			runDssCommand(f'new object=monitor.{mon_name} element={obType}.{name} terminal=1 mode=6')
			mon_names.append(mon_name)
		elif ob.get('object','').startswith('transformer.'):
			#TODO: only capture transformers with regulators on them by looking through the regcontrol objects.
			runDssCommand(f'new object=monitor.{mon_name} element={obType}.{name} terminal=1 mode=2')
			mon_names.append(mon_name)
	# Run DSS
	runDssCommand(f'set mode=yearly stepsize={stepSizeInMinutes}m')
	if actions == {}:
		# Run all steps directly.
		runDssCommand(f'set number={numberOfSteps}')
		runDssCommand('solve')
	else:
		# Actions defined, run them at the appropriate timestep.
		runDssCommand(f'set number=1')
		for step in range(1, numberOfSteps+1):
			action = actions.get(step)
			if action != None:
				print(f'Step {step} executing:', action)
				runDssCommand(action)
			runDssCommand('solve')
	# Export all monitors
	for name in mon_names:
		runDssCommand(f'export monitors monitorname={name}')
	# Aggregate monitors
	all_gen_df = pd.DataFrame()
	all_load_df = pd.DataFrame()
	all_source_df = pd.DataFrame()
	all_control_df = pd.DataFrame()
	for name in mon_names:
		csv_path = f'{dssFileLoc}/{circ_name}_Mon_{name}.csv'
		df = pd.read_csv(f'{circ_name}_Mon_{name}.csv')
		if name.startswith('monload-'):
			df['Name'] = name
			all_load_df = pd.concat([all_load_df, df], ignore_index=True, sort=False)
		elif name.startswith('mongenerator-'):
			df['Name'] = name
			all_gen_df = pd.concat([all_gen_df, df], ignore_index=True, sort=False)
		elif name.startswith('monvsource-'):
			df['Name'] = name
			all_source_df = pd.concat([all_source_df, df], ignore_index=True, sort=False)
		elif name.startswith('moncapacitor-'):
			df['Type'] = 'Capacitor'
			df['Name'] = name
			df = df.rename({' Step_1 ': 'Tap(pu)'}, axis='columns') #HACK: rename to match regulator tap name
			all_control_df = pd.concat([all_control_df, df], ignore_index=True, sort=False)
		elif name.startswith('montransformer-'):
			df['Type'] = 'Transformer'
			df['Name'] = name
			df = df.rename({' Tap (pu)': 'Tap(pu)'}, axis='columns') #HACK: rename to match cap tap name
			all_control_df = pd.concat([all_control_df, df], ignore_index=True, sort=False)
		if not keepAllFiles:
			os.remove(csv_path)
	# Write final aggregates
	all_gen_df.sort_values(['Name','hour'], inplace=True)
	all_gen_df.columns = all_gen_df.columns.str.replace(r'[ "]','')
	all_gen_df.to_csv(f'{dssFileLoc}/timeseries_gen.csv', index=False)
	all_control_df.sort_values(['Name','hour'], inplace=True)
	all_control_df.columns = all_control_df.columns.str.replace(r'[ "]','')
	all_control_df.to_csv(f'{dssFileLoc}/timeseries_control.csv', index=False)
	all_source_df.sort_values(['Name','hour'], inplace=True)
	all_source_df.columns = all_source_df.columns.str.replace(r'[ "]','')
	all_source_df["P1(kW)"] = all_source_df["V1"] * all_source_df["I1"] / 1000.0
	all_source_df["P2(kW)"] = all_source_df["V2"] * all_source_df["I2"] / 1000.0
	all_source_df["P3(kW)"] = all_source_df["V3"] * all_source_df["I3"] / 1000.0
	all_source_df.to_csv(f'{dssFileLoc}/timeseries_source.csv', index=False)
	all_load_df.sort_values(['Name','hour'], inplace=True)
	all_load_df.columns = all_load_df.columns.str.replace(r'[ "]','')
	all_load_df.to_csv(f'{dssFileLoc}/timeseries_load.csv', index=False)

def voltagePlot(filePath, PU=True):
	''' Voltage plotting routine. Creates 'voltages.csv' and 'Voltage [PU|V].png' in directory of input file.'''
	# TODO: use getVoltages() here
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	# TODO: use getCoords() here, if we write it.
	#volt_coord = runDSS(filePath, keep_output=False)
	volt_coord = runDSS(filePath)
	runDssCommand('Export voltages "' + dssFileLoc + '/volts.csv"')
	voltage = pd.read_csv(dssFileLoc + '/volts.csv')
	# Generate voltage plots.
	volt_coord.columns = ['Bus', 'X', 'Y', 'radius'] # radius would be obtained by getCoords().
	voltageDF = pd.merge(volt_coord, voltage, on='Bus') # Merge on the bus axis so that all data is in one frame.
	plt.title('Voltage Profile')
	plt.xlabel('Distance from source[miles]')
	if PU:
		for i in range(1, 4): 
			volt_ind = ' pu' + str(i)
			plt.scatter(voltageDF['radius'], voltageDF[volt_ind], label='Phase ' + str(i))
		plt.ylabel('Voltage [PU]')
		plt.legend()
		plt.savefig(dssFileLoc + '/Voltage Profile [PU].png')
	else:
		# plt.axis([1, 7, 2000, 3000]) # Ignore sourcebus-much greater-for overall magnitude.
		for i in range(1, 4): 
			mag_ind = ' Magnitude' + str(i)
			plt.scatter(voltageDF['radius'], voltageDF[mag_ind], label='Phase ' + str(i))
		plt.ylabel('Voltage [V]')
		plt.legend()
		plt.savefig(dssFileLoc + '/Voltage Profile [V].png')
	plt.clf()

def currentPlot(filePath):
	''' Current plotting function.'''
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	curr_coord = runDSS(filePath)
	runDssCommand('Export currents "' + dssFileLoc + '/currents.csv"')
	current = pd.read_csv(dssFileLoc + '/currents.csv')
	curr_coord.columns = ['Index', 'X', 'Y', 'radius'] # DSS buses don't have current, but are connected to it. 
	curr_hyp = []
	currentDF = pd.concat([curr_coord, current], axis=1)
	plt.xlabel('Distance from source [km]')
	plt.ylabel('Current [Amps]')
	plt.title('Current Profile')
	for i in range(1, 3):
		for j in range(1, 4):
			cur_ind = ' I' + str(i) + '_' + str(j)
			plt.scatter(currentDF['radius'], currentDF[cur_ind], label=cur_ind)
	plt.legend()
	plt.savefig(dssFileLoc + '/Current Profile.png')
	plt.clf()

def networkPlot(filePath):
	''' Plot the physical topology of the circuit. '''
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	coords = runDSS(filePath)
	runDssCommand('Export voltages "' + dssFileLoc + '/volts.csv"')
	volts = pd.read_csv(dssFileLoc + '/volts.csv')
	coords.columns = ['Bus', 'X', 'Y', 'radius']
	G = nx.Graph()
	# Get the coordinates.
	pos = {}
	for index, row in coords.iterrows():
		try:
			bus_name = str(int(row['Bus']))
		except:
			bus_name = row['Bus']
		G.add_node(bus_name)
		pos[bus_name] = (row['X'], row['Y'])
 	# Get the connecting edges using Pandas.
	lines = dss.utils.lines_to_dataframe()
	edges = []
	for index, row in lines.iterrows():
		#HACK: dss upercases everything in the outputs.
		bus1 = row['Bus1'][:4].upper().replace('.', '')
		bus2 = row['Bus2'][:4].upper().replace('.', '')
		edges.append((bus1, bus2))
	G.add_edges_from(edges)
	# We'll color the nodes according to voltage.
	volt_values = {}
	labels = {}
	for index, row in volts.iterrows():
		volt_values[row['Bus']] = row[' pu1']
		labels[row['Bus']] = row['Bus']
	colorCode = [volt_values.get(node, 0.0) for node in G.nodes()]
	# Start drawing.
	nodes = nx.draw_networkx_nodes(G, pos, node_color=colorCode)
	edges = nx.draw_networkx_edges(G, pos)
	nx.draw_networkx_labels(G, pos, labels, font_size=8)
	plt.colorbar(nodes)
	plt.xlabel('Distance [m]')
	plt.title('Network Voltage Layout')
	plt.savefig(dssFileLoc + '/networkPlot.png')
	plt.clf()

def THD(filePath):
	''' Calculate and plot total harmonic distortion. '''
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	bus_coords = runDSS(filePath)
	runDssCommand('Solve mode=harmonics')
	runDssCommand('Export voltages "' + dssFileLoc + '/voltharmonics.csv"')
	# Clean up temp file.
	try:
		base = os.path.basename(filePath)
		fnameMinusExt = os.path.splitext(base)[0]
		os.remove('{}_SavedVoltages.dbl'.format(fnameMinusExt))
	except:
		pass
	voltHarmonics = pd.read_csv(dssFileLoc + '/voltharmonics.csv')
	bus_coords.columns = ['Bus', 'X', 'Y', 'radius']
	voltHarmonics.columns.str.strip()
	for index, row in voltHarmonics.iterrows():
		voltHarmonics['THD'] = row[' Magnitude1']/(math.sqrt(row[' Magnitude2']**2 + row[' Magnitude3']**2))
	distortionDF = pd.merge(bus_coords, voltHarmonics, on='Bus') # Merge on the bus axis so that all data is in one frame.
	plt.scatter(distortionDF['radius'], distortionDF['THD'])
	plt.xlabel('Distance from Source [miles]')
	plt.ylabel('THD [Percentage]')
	plt.title('Total Harmonic Distortion')
	plt.savefig(dssFileLoc + '/THD.png')
	plt.clf()

def dynamicPlot(filePath, time_step, iterations):
	''' Do a dynamic, long-term study of the powerflow. time_step is in seconds. '''
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))	
	runDSS(filePath)
	runDssCommand('Solve')
	dynamicCommand = 'Solve mode=dynamics stepsize=%d number=%d' % (time_step, iterations)
	runDssCommand(dynamicCommand)
	for i in range(iterations):
		voltString = 'Export voltages "' + dssFileLoc + '/dynamicVolt%d.csv"' % i
		currentString = 'Export currents "' + dssFileLoc + '/dynamicCurrent%d.csv"' % i
		runDssCommand(voltString)
		runDssCommand(currentString)
	powerData = []
	for j in range(iterations):
		curVolt = 'dynamicvolt%d.csv' % j
		curCurrent = 'dynamiccurrent%d.csv' % j
		voltProfile = pd.read_csv(dssFileLoc + '/' + curVolt)
		voltProfile.columns = voltProfile.columns.str.replace(' ', '')
		curProfile = pd.read_csv(dssFileLoc + '/' + curCurrent)
		curProfile.columns = curProfile.columns.str.replace(' ', '')
		sourceVoltage = voltProfile.loc[voltProfile['Bus'] == 'SOURCEBUS']
		sourceCurrent = curProfile.loc[curProfile['Element'] == 'Vsource.SOURCE']
		data_summary = {'Volts': (sourceVoltage['Magnitude1'], sourceVoltage['Magnitude2'], sourceVoltage['Magnitude3']), 
		'Currents': (sourceCurrent['I1_1'], sourceCurrent['I1_2'], sourceCurrent['I1_3'])}
		power_triplet = (data_summary['Volts'][0]*data_summary['Currents'][0], data_summary['Volts'][1]*data_summary['Currents'][1], data_summary['Volts'][2]*data_summary['Currents'][2])
		powerData.append(power_triplet)
	first_phase = [item[0] for item in powerData]
	second_phase = [item[1] for item in powerData]
	third_phase = [item[2] for item in powerData]
	plt.plot(first_phase, label='Phase one')
	plt.plot(second_phase, label='Phase two')
	plt.plot(third_phase, label='Phase three')
	plt.legend()
	plt.xlim(0, iterations-1)
	plt.xlabel('Time [s]')
	plt.ylabel('Power [kW]')
	plt.title('Dynamic Simulation Power Plot')
	plt.savefig(dssFileLoc + '/DynamicPowerPlot.png')
	os.system('rm ' + dssFileLoc + '/dynamicvolt* ' + dssFileLoc + '/dynamiccurrent*')

def faultPlot(filePath):
	''' Plot fault study. ''' 
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	bus_coord = runDSS(filePath)
	runDssCommand('Solve Mode=FaultStudy')
	runDssCommand('Export fault "' + dssFileLoc + '/faults.csv"')
	faultData = pd.read_csv(dssFileLoc + '/faults.csv')
	bus_coord.columns = ['Bus', 'X', 'Y', 'radius']
	faultDF = pd.concat([bus_coord, faultData], axis=1)
	faultDF.columns = faultDF.columns.str.strip()
	plt.axis([-1, 6, 0, 8000])
	plt.xlabel('Distance From Source [Miles]')
	plt.ylabel('Current [Amps]')
	plt.title('Fault Study')
	plt.scatter(faultDF['radius'], faultDF['3-Phase'], label='3-Phase to Ground')
	plt.scatter(faultDF['radius'], faultDF['1-Phase'], label='1-Phase to Ground')
	plt.scatter(faultDF['radius'], faultDF['L-L'], label='Line-to-Line')
	plt.legend()
	plt.savefig(dssFileLoc + '/Fault Currents.png')
	plt.clf()

def capacityPlot(filePath):
	''' Plot power vs. distance '''
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	coords = runDSS(filePath)
	runDssCommand('Export Capacity "' + dssFileLoc + '/capacity.csv"')
	capacityData = pd.read_csv(dssFileLoc + '/capacity.csv')
	coords.columns = ['Index', 'X', 'Y', 'radius']
	capacityDF = pd.concat([coords, capacityData], axis=1)
	#TODO set any missing buscoords to (0,0) or remove NaN rows using dataframe.dropna(). Currently fails iowa240 without this fix.
	fig, ax1 = plt.subplots()
	ax1.set_xlabel('Distance From Source [Miles]')
	ax1.set_ylabel('Power [kW]')
	ax1.scatter(capacityDF['radius'], capacityData[' kW'], label='Power')
	ax2 = ax1.twinx()
	ax2.set_ylabel('Maximum transformer percentage (One-side)')
	ax2.scatter(capacityDF['radius'], capacityDF.iloc[:, 2]+capacityDF.iloc[:, 3], label='Transformer Loading', color='red')
	fig.tight_layout() # otherwise the right y-label is slightly clipped
	fig.legend()
	plt.savefig(dssFileLoc + '/Capacity Profile.png')
	plt.clf()
	
def voltageCompare(in1, in2, saveascsv=False, with_plots=False, outdir='', outfilebase='voltageCompare'):
	'''Compares two instances of the information provided by the 'Export voltages' opendss command and outputs 
	the maximum error (% and absolute difference) encountered for any value compared. If the 'keep_output' flag is set to 'True', also 
	outputs a file that describes the maximum, average, and minimum error encountered for each column. Use the 
	'output_filename' parameter to set the output file name. Inputs can be formatted as a .dss file of voltages
	output by OpenDSS, or as a dataframe of voltages obtained using the OMF's getVoltages().'''
	#TODO: rewrite description
	#TODO: set in1 as predicted/modded/final and handle it as such; in1 is the truth/original/initial
	ins = [in1, in2]
	txtins = [x for x in ins if type(x)==str and 'dss'==x.lower().split('.')[-1]]
	memins = [x for x in ins if type(x)==pd.DataFrame]
	assert (len(txtins)+len(memins))==2, 'Inputs must either be a .dss file of voltages as output by the OpenDss \'Export Voltages\' command, or a dataframe of voltages output by the omf method \'getVoltages()\'.'
	# Convert .csvs to dataframes and add to the list
	for pth in txtins:
		df = pd.DataFrame()
		df = pd.read_csv(pth, header=0)
		df.index = df['Bus']
		df.drop(labels='Bus', axis=1, inplace=True)
		df = df.astype(float, copy=True)
		memins.append(df)
	# Which has more rows? We'll define the larger one to be 'avolts'. This is also considered the 'theoretical' set.
	foob = 0 if len(memins[0].index) > len(memins[1].index) else 1
	avolts = memins[foob]
	foob = 1-foob # returns 0 if foob==1 ; returns 1 if foob==0
	bvolts = memins[foob]
	# Match columns to rows, perform needed math, and save into resultErr.
	cols = avolts.columns
	cols = [c for c in cols if (not c.startswith(' pu')) and (not c.startswith(' Node'))]
	resultErrD = pd.DataFrame(index=avolts.index, columns=cols)
	resultErrP = resultErrD.copy()
	# TODO can this code block be sped up?
	for col in cols:
		for row in avolts.index:
			if not row in bvolts.index:
				continue
			in1 = avolts.loc[row,col]
			in2 = bvolts.loc[row,col]
			resultErrP.loc[row,col] = 100*(in1 - in2)/in1 if in1!=0 else 0
			resultErrD.loc[row,col] = in1 - in2
	# Construct results
	resultSummP = pd.DataFrame(index=['Max %Err', 'Avg %Err', 'Min %Err', 'RMSPE'], columns=cols)
	resultSummD = pd.DataFrame(index=['Max Diff', 'Avg Diff', 'Min Diff', 'RMSE'], columns=cols)
	for c in cols:
		resultSummP.loc['Max %Err',c] = resultErrP.loc[:,c].max(skipna=True)
		resultSummP.loc['Avg %Err',c] = resultErrP.loc[:,c].mean(skipna=True)
		resultSummP.loc['Min %Err',c] = resultErrP.loc[:,c].min(skipna=True)
		resultSummP.loc['RMSPE',c] = math.sqrt((resultErrP.loc[:,c]**2).mean())
		resultSummD.loc['Max Diff',c] = resultErrD.loc[:,c].max(skipna=True)
		resultSummD.loc['Avg Diff',c] = resultErrD.loc[:,c].mean(skipna=True)
		resultSummD.loc['Min Diff',c] = resultErrD.loc[:,c].min(skipna=True)
		resultSummD.loc['RMSE',c] = math.sqrt((resultErrD.loc[:,c]**2).mean())
	if saveascsv:
		outroot = outdir + '/' + outfilebase
		resultErrP.dropna(inplace=True)
		resultSummP.to_csv(outroot + '_Perc.csv', header=True, index=True, mode='w')
		emptyline = pd.DataFrame(index=[''],columns=cols)
		emptyline.to_csv(outroot + '_Perc.csv', header=False, index=True, mode='a')
		resultErrP.to_csv(outroot + '_Perc.csv', header=True, index=True, mode='a')
		resultErrD.dropna(inplace=True)
		resultSummD.to_csv(outroot + '_Diff.csv', header=True, index=True, mode='w')
		emptyline.to_csv(outroot + '_Diff.csv', header=False, index=True, mode='a')
		resultErrD.to_csv(outroot + '_Diff.csv', header=True, index=True, mode='a')
	if with_plots:
		# Produce boxplots to visually analyze the residuals
		from matplotlib.pyplot import boxplot
		magcols = [c for c in cols if c.lower().startswith(' magnitude')]
		bxpltMdf = pd.DataFrame(index=bvolts.index,data=resultErrD,columns=magcols)
		bxpltM = []
		for item in magcols:
			bxpltM.append(bxpltMdf[item])
		figM, axM = plt.subplots()
		axM.set_title('Boxplot of Residuals: Voltage Magnitude')
		plt.xticks(rotation=45)
		axM.set_xticklabels(magcols)
		axM.boxplot(bxpltM)
		figM.savefig(outroot + '_boxplot_Mag.png', bbox_inches='tight')
		plt.close()
		angcols = [c for c in cols if c.lower().startswith(' angle')]
		bxpltAdf = pd.DataFrame(data=resultErrD[angcols],columns=angcols)
		bxpltA = []
		for item in angcols:
			bxpltA.append(bxpltAdf[item])
		figA, axA = plt.subplots()
		axA.set_title('Boxplot of Residuals: Voltage Angle')
		plt.xticks(rotation=45)
		axA.set_xticklabels(angcols)
		axA.boxplot(bxpltA)
		figA.savefig(outroot + '_boxplot_Ang.png', bbox_inches='tight')
		plt.close()
		for c in cols:
			# construct a dataframe of busname, input, output, and residual
			dat = pd.concat([avolts[c],bvolts[c],resultErrP[c],resultErrD[c]], axis=1,join='inner')
			dat.columns = ['buses+','buses-','residuals_P','residuals_D'] # buses+ denotes the circuit with more buses; buses- denotes the one with fewer
			dat = dat.sort_values(by=['buses-','buses+'], ascending=True, na_position='first')
			# Produce plot of residuals
			#pltlenR = math.ceil(len(dat['residuals_P'])/2)
			#figR, axR = plt.subplots(figsize=(pltlenR,12))
			#axR.plot(dat['buses-'], 'k.', alpha=0.15)
			figR, axR = plt.subplots()
			axR.plot(dat['buses-'], dat['residuals_P'], 'k.', alpha=0.15)
			axR.set_title('Plot of Residuals: ' + c)
			#plt.xticks(rotation=45)
			axR.set_xlabel('Value of ' + c + ' for circuit with fewer buses')
			axR.set_ylabel('Value of Residual')
			figR.savefig(outroot + '_residualplot_' + c +'_.png', bbox_inches='tight')
			plt.close()
			# Produce scatter plots
			figS, axS = plt.subplots()
			axS.set_title('Scatter Plot: ' + c)
			axS.plot(dat['buses-'], dat['buses+'], 'k.', alpha=0.15)
			axS.set_xlabel('Value of ' + c + ' for circuit with fewer buses')
			axS.set_ylabel('Value of ' + c + ' for circuit with more buses')
			figS.savefig(outroot + '_scatterplot_' + c +'_.png', bbox_inches='tight')
			plt.close()
	return resultSummP, resultSummD

def getVoltages(dssFilePath, keep_output=False, outdir='', output_filename='voltages.csv'): # TODO: rename to voltageGet for consistency with other functions?
	'''Obtains the OpenDss voltage output for a OpenDSS circuit definition file (*.dss). Input path 
	can be fully qualified or not. Set the 'keep_output' flag to 'True' to save output to the input 
	file's directory as 'voltages.csv',	or specify a filename for the output through the 
	'output_filename' parameter (i.e. '*.csv').'''
	dssFileLoc = os.path.dirname(os.path.abspath(dssFilePath))
	coords = runDSS(os.path.abspath(dssFilePath), keep_output=False)
	if outdir!='':
		outdir = outdir + '/'
	voltfile = dssFileLoc + '/' + outdir + output_filename
	runDssCommand('Export voltages "' + voltfile + '"')
	volts = pd.read_csv(voltfile, header=0)
	volts.index = volts['Bus']
	volts.drop(labels='Bus', axis=1, inplace=True)
	volts = volts.astype(float, copy=True)
	if not keep_output:
		os.remove(voltfile)
	return volts

def applyCnxns(tree):
	'''Gathers and applies connection information to dss lines and buses.'''
	relevantObjs = ['capacitor','line','transformer','load','reactor','monitor','energymeter','generator','pvsystem','vsource','relay','fuse']
	# make a mapping between an object's name and its index in tree
	name2key = {v.get('bus', None):i for i,v in enumerate(tree) if v.get('!CMD','NC')=='setbusxy'}
	name2key.update({v.get('object', None):i for i,v in enumerate(tree) if v.get('!CMD','NC')=='new'})
	for obj in tree:
		objid = obj.get('object','None')
		if objid.split('.')[0] not in relevantObjs:
			continue
		cnxns = []
		for k,v in obj.items():
			if k == 'buses':
				bb = v
				bb = bb.replace(']','')
				bb = bb.replace('[','')
				bb = bb.split(',')
				for b in bb:
					cnxns.append(b.split('.')[0])
			elif k in ['bus','bus1','bus2']:
				cnxns.append(v.split('.')[0])
			elif k in ['element','monitoredobj']:
				cnxns.append(v)
		for cnxn in cnxns:
			if cnxn in name2key:
				# get existing connections, append, and reassign to tree
				treebusobj = tree[name2key[cnxn]]
				if '!CNXNS' in treebusobj:
					bb = treebusobj['!CNXNS']
					treebusobj['!CNXNS'] = bb.replace(']', ',' + objid + ']')
				else:
					treebusobj['!CNXNS'] = '[' + objid + ']'
			elif len(cnxn.split('.'))==1:
				# make a new entry in the tree and update name2key
				from collections import OrderedDict 
				newobj = OrderedDict([
					('!CMD','new'),
					('object',cnxn),
					('x','0'),
					('y','0'),
					('!CNXNS','[' + objid + ']')
					])
				tree.append(newobj)
				newdict = {cnxn:len(tree)-1}
				name2key.update(newdict)
			else:
				print('opendss.applyCnxns() reports an unprocessed item: %s\n'%(cnxn))
	return tree

def removeCnxns(tree):
	for i,obj in enumerate(tree.copy()):
		if obj.get('!CNXNS','NCX')!='NCX':
			del tree[i]['!CNXNS']
	return tree

def _mergeContigLinesOnce(tree):
	'''Reduces circuit complexity by combining adjacent line segments having identical configurations.'''
	# Applicable circuit model: [top bus]-[top line]-[middle bus]-[bottom line]-[bottom bus]-...
	from copy import deepcopy
	treeids = range(0,len(tree),1)
	tree = dict(zip(treeids,tree))
	name2key = {v.get('object', None):k for k,v in tree.items()}
	name2key.update({v.get('bus', None):k for k,v in tree.items() if v.get('!CMD', None) == 'setbusxy'})
	# Iterate through treecopy and perform any modifications directly on tree. Note that name2key can be used om either tree or treecopy.
	treecopy = deepcopy(tree)
	removedids = []
	for topobj in treecopy.values():
		top = topobj.copy()
		topid = top.get('object','None')
		# is this a line object?
		if not topid.startswith('line.'):
			continue
		# has this line already been removed?
		if topid in removedids:
			continue
		# Is the top a switch? Let's skip these for now. TODO: handling for switches when merging them with adjacent line segments is feasible
		if top.get('switch','None') in ['true','yes']:
			continue
		# Get the 'to' bus
		midbusid = top.get('bus2','NA')
		if midbusid=='NA':
			continue 
		midbus = treecopy[name2key[midbusid.split('.')[0]]]
		# Get ids of the relevant objects (other than the top) connected to the parent bus (aka the bottoms)
		bottoms = midbus.get('!CNXNS','None')
		bottoms = bottoms.replace('[','').replace(']','')
		bottoms = bottoms.split(',')
		bottoms.remove(topid)
		# Check for a one-line-in, one-line-out scenario
		if len(bottoms) != 1:
			continue
		botid = bottoms[0]
		bottom = treecopy[name2key[botid]]
		if not bottom.get('object','None').startswith('line.'):
			continue
		# Is the bottom a switch? Let's skip these for now. TODO: handling for switches when merging them with adjacent line segments is feasible
		if bottom.get('switch','None') in ['true','yes']:
			continue
		# Does the bottom have any other objects 'attached' to it? If so, we must not remove it. 
		if bottom.get('!CNXNS','NCX')!='NCX':
			continue
		# All checks have passed. Let's combine the top and bottom lines.
		if ('length' in top) and ('length' in bottom):
			# check that the configurations are equal
			diffprops = ['!CMD','object','bus1','bus2','length','!CNXNS'] # we don't care if these values differ between the top and the bottom
			continueFlag = False
			for k,vt in top.items():
				if not k in diffprops:
					vb = bottom.get(k,'None')
					if vt!=vb:
						continueFlag = True
						break
			if continueFlag:
				continueFlag = False
				continue
			# Set top line length = sum of both lines
			newLen = float(top['length']) + float(bottom['length']) # get the new length
			top['length'] = str(newLen)
			# Connect top line to the bottom bus
			top['bus2'] = bottom['bus2']
			tree[name2key[topid]] = top
			# Connect bottom bus to the top line 
			botbus = treecopy[name2key[bottom['bus2'].split('.')[0]]].copy()
			botbcons = botbus.get('!CNXNS','None')
			botbcons = botbcons.replace('[','').replace(']','')
			botbcons = botbcons.split(',')
			if bottom['object'] in botbcons:
				iji = botbcons.index(bottom['object'])
				botbcons[iji] = top['object']
			tstr = '['
			for item in botbcons:
				tstr = tstr + item + ','
			tstr = tstr[:-1] + ']'
			botbus['!CNXNS'] = tstr
			tree[name2key[botbus['bus']]] = botbus
			# Delete the bottom line element and the middle bus			
			removedids.append(bottom['object'])
			del tree[name2key[bottom['object']]]
			removedids.append(midbus['bus'])
			del tree[name2key[midbus['bus']]]
	with open('removed_ids.txt', 'a') as remfile:
		for remid in removedids:
			remfile.write(remid + '\n')
	return [v for k,v in tree.items()] # back to a list of dicts

def mergeContigLines(tree):
	''' merge all lines that are across nodes and have the same config
	topline --to-> node <-from-- bottomline'''
	tree = applyCnxns(tree)
	removedKeys = 1
	if os.path.exists('removed_ids.txt'):
		os.remove('removed_ids.txt')
	while removedKeys != 0:
		treeKeys = len(tree)
		tree = _mergeContigLinesOnce(tree)
		removedKeys = treeKeys - len(tree)
	tree = removeCnxns(tree)
	return tree

def rollUpOnePhaseLoads(tree):
	'''Combines complex load distribution circuits into a single electrically-representative load. Applies to instances where one or more 
	single-phase loads are connected to a single bus. If that bus is also connected to a transformer via one or more line segments, 
	these are also consolidated. Does not apply to split-phase configurations.'''
	# Applicable circuit model: [one or more loads]-[bus]-[zero or more lines]-[bus]-[transformer (optional)]-...
	tree = applyCnxns(tree)
	from copy import deepcopy
	treeids = range(0,len(tree),1)
	tree = dict(zip(treeids,tree))
	name2key = {v.get('object', None):k for k,v in tree.items()}
	name2key.update({v.get('bus', None):k for k,v in tree.items() if v.get('!CMD', None) == 'setbusxy'})
	# Iterate through treecopy and perform any modifications directly on tree. Note that name2key can be used on either tree or treecopy.
	treecopy = deepcopy(tree)
	removedids = []
	for obj in treecopy.values():
		objid = obj.get('object','None')
		# Is this a load object? If not, move to next object in treecopy
		if not objid.startswith('load.'):
			continue
		# Has this load already been removed?
		if objid in removedids:
			continue
		# Get the load's parent bus
		loadbusid = obj.get('bus1','None').split('.')[0]
		loadbus = treecopy[name2key[loadbusid]]
		# Get everything that is attached to the parent bus
		siblings = loadbus.get('!CNXNS','None')
		siblings = siblings.replace('[','').replace(']','')
		siblings = siblings.split(',')
		# Grab load objects and check that there is more than one
		loadids = [x for x in siblings if x.startswith('load')]
		loads = [treecopy[name2key[x]] for x in loadids]
		if len(loads) == 1:
			continue
		# For now, only handle cases of 3 single-phase loads connected to a 3-phase line 
		# TODO: Consider 2 single-phase loads connected directly to two-phases of a line
		if len(loads) != 3:
			continue
		# Loop through loads to perform some checks and get some values
		newkw = 0
		newkvar = 0
		continueFlag = False
		diffprops = ['!CMD','object','bus1','!CNXNS','!CONNCODE','numcust','kw','kvar'] # we don't care if these values differ between the loads
		for i, load in enumerate(loads): # TODO: check for equivalent connection config (i.e. wye or delta)?
			# check that relevant load configurations are equal
			# TODO: Consider unequal voltages?
			if i==0:
				lastload = load
				continue
			for k,v in load.items():
				if not k in diffprops:
					if lastload.get(k,'None') != v:
						continueFlag = True # we don't care about combining this group of loads, so move on to next load in tree
						break	
			if continueFlag:
				break # leave continueFlag set to True to break out of outer 'for' loop
			# Check for single-phase
			numnodes = len(load['bus1'].split('.'))-1
			if numnodes!=1:
				# TODO: Consider one-phase connections defined as .x.0 or .0.x. 
				continueFlag = True
				break
			# Capture kw and kvar
			newkw = newkw + float(load.get('kw','0'))
			newkvar = newkvar + float(load.get('kvar','0'))
			# prepare for the next loop
			lastload = load
		if continueFlag:
			continueFlag = False
			continue
		# combine into one n-phase load
		# TODO: consider wye vs delta connections for total kw and kvar calculations
		# 	wye:	loads connect line-to-neutral.
		# 	delta:	loads connect line-to-line. 
		# TODO: detect and preserve connection order other than .1.2.3 or .1.2 or .0.1 or .0.2. see ieee37 for examples of .3.1
		newload = tree[name2key[objid]]
		newload['kw'] = str(newkw) # Does this calculation require sqrt(3) somewhere?
		newload['kvar'] = str(newkvar)
		newbusid = newload['bus1'].split('.')[0]
		newload['bus1'] = newbusid + '.1.2.3'
		newload['phases'] = '3'
		# Remove the deleted loads from the bus !CNXNS 
		newbus = tree[name2key[newbusid]]
		newbcons = newbus.get('!CNXNS','None')
		newbcons = newbcons.replace('[','').replace(']','')
		newbcons = newbcons.split(',')
		loadids.remove(objid) # now only contains the removed load ids
		for loadid in loadids:
			if loadid in newbcons:
				newbcons.remove(loadid)
		tstr = '['
		for item in newbcons:
			tstr = tstr + item + ','
		tstr = tstr[:-1] + ']'
		newbus['!CNXNS'] = tstr
		tree[name2key[newbusid]] = newbus
		# delete removed loads from tree
		for loadid in loadids:
			removedids.append(loadid)
			del tree[name2key[loadid]]
			if name2key[loadid] in tree:
				hfop = 'irfbowrf'
		## interesting cases:
		# ieee37
		# 	-bus 712. one line and one load. is there a transformer upstream of the line? If not, there would be two lines wouldn't there? NO. Not in the case of loads connected between two phases, which happens frequently.



		## Do the siblings include a transformer?
		#xfmrs = [x for x in siblings if x.get('object','None').startswith('transformer')]
		#if len(xfmrs)!=1:
		#	continue
		#xfmr = xfmrs[0]
		#xfmrbuses = xfmr.get('buses','None') # Note: It is expected that the primary winding of the transformer is defined first in the 'buses' array

		# Capture load kws and associate with appropiate %r in a dataframe 
		#ldparams = pd.DataFrame(columns=['node','kw','perc_r'])
		#for ld in loads:
		#	kw = ld.get('kw','DNE')
		#	node = ''
		#	pass
		#kws = [x.get('kw') for x in loads if x.get('kw','DNE')!='DNE']
		
		## Note: We assume that info for the high side (aka the line side) of the xfrmr is in position 0 of the config arrays
		#r_arr = xfmr.get('%rs','None')

		## Calculate what the equivalent load should be
		#secLoad = 0
		#for idx,row in ldparams.iterrows():
		#	secLoad = secLoad + row['kw']*(1+row['perc_r'])
		##load_eq = (1 + r_prim)*secLoad
	tree = [v for k,v in tree.items()] # back to a list of dicts
	tree = removeCnxns(tree)
	if os.path.exists('removed_ids.txt'):
		os.remove('removed_ids.txt')
	with open('removed_ids.txt', 'a') as remfile:
		for remid in removedids:
			remfile.write(remid + '\n')
	return tree

def rollUpSplitPhaseLoads(tree):
	'''Just a wrapper for future endeavors.'''
	tree = applyCnxns(tree)
	from copy import deepcopy
	treeids = range(0,len(tree),1)
	tree = dict(zip(treeids,tree))
	name2key = {v.get('object', None):k for k,v in tree.items()}
	name2key.update({v.get('bus', None):k for k,v in tree.items() if v.get('!CMD', None) == 'setbusxy'})
	# Iterate through treecopy and perform any modifications directly on tree. Note that name2key can be used on either tree or treecopy.
	treecopy = deepcopy(tree)
	removedids = []
	for obj in treecopy.values():

		pass # Code goes here
	
	tree = [v for k,v in tree.items()] # back to a list of dicts
	tree = removeCnxns(tree)
	if os.path.exists('removed_ids.txt'):
		os.remove('removed_ids.txt')
	with open('removed_ids.txt', 'a') as remfile:
		for remid in removedids:
			remfile.write(remid + '\n')
	tree = removeCnxns(tree)
	return tree


def _tests():
	from dssConvert import dssToTree, distNetViz, evilDssTreeToGldTree, treeToDss, evilGldTreeToDssTree
	fpath = ['ieee37.clean.dss','ieee123_solarRamp.clean.dss','iowa240.clean.dss','ieeeLVTestCase.clean.dss','ieee8500-unbal_no_fuses.clean.dss']

	for ckt in fpath:
		print('!!!!!!!!!!!!!! ',ckt,' !!!!!!!!!!!!!!')
		# Test for mergeContigLines, voltageCompare, getVoltages, and runDSS.
		tree = dssToTree(ckt)
		#gldtree = evilDssTreeToGldTree(tree) # DEBUG
		#distNetViz.viz_mem(gldtree, open_file=True, forceLayout=True) # DEBUG
		oldsz = len(tree)
		tree = mergeContigLines(tree)
		#tree = rollUpOnePhaseLoads(tree)
		newsz = len(tree)
		#gldtree = evilDssTreeToGldTree(tree) # DEBUG
		#distNetViz.viz_mem(gldtree, open_file=True, forceLayout=True) # DEBUG
		#tree = evilGldTreeToDssTree(gldtree) # DEBUG
		outckt_loc = ckt[:-4] + '_reduced.dss'
		treeToDss(tree, outckt_loc)

		outdir = 'voltageCompare_' + ckt[:-4]
		if not os.path.exists(outdir):
			os.mkdir(outdir)
		involts_loc = ckt[:-4] + '_volts.dss'
		involts = getVoltages(ckt, keep_output=True, outdir=outdir, output_filename=involts_loc)
		outvolts_loc = outckt_loc[:-4] + '_volts.dss'
		outvolts = getVoltages(outckt_loc, keep_output=True, outdir=outdir, output_filename=outvolts_loc)
		rsumm_P, rsumm_D = voltageCompare(involts, outvolts, saveascsv=True, with_plots=False, outdir=outdir, outfilebase=ckt[:-4])		
		maxPerrM = [rsumm_P.loc['RMSPE',c] for c in rsumm_P.columns if c.lower().startswith(' magnitude')]
		maxPerrM = pd.Series(maxPerrM).max()
		maxPerrA = [rsumm_P.loc['RMSPE',c] for c in rsumm_P.columns if c.lower().startswith(' angle')]
		maxPerrA = pd.Series(maxPerrA).max()
		maxDerrA = [rsumm_D.loc['RMSE',c] for c in rsumm_D.columns if c.lower().startswith(' angle')]
		maxDerrA = pd.Series(maxDerrA).max()
		maxDerrM = [rsumm_D.loc['RMSE',c] for c in rsumm_D.columns if c.lower().startswith(' magnitude')]
		maxDerrM = pd.Series(maxDerrM).max()
		from shutil import rmtree
		os.remove(outckt_loc)
		rmtree(outdir)
		errlim = 0.03 # threshold of 30% error between reduced files. 
		assert maxPerrM <= errlim, 'The voltage magnitude error between the compared files exceeds the allowable limit of %s%%.'%(errlim*100)
		#print('Objects removed: %s (of %s).\nPercent reduction: %s%%\nMax RMSPE for voltage magnitude: %s%%\nMax RMSPE for voltage angle: %s%%\nMax RMSE for voltage magnitude: %s\nMax RMSE for voltage angle: %s\n'%(oldsz-newsz, oldsz, (oldsz-newsz)*100/oldsz, maxPerrM, maxPerrA, maxDerrM, maxDerrA)) # DEBUG
		

	# Make core output
	#FPATH = 'iowa240.clean.dss'
	#FPATH = 'ieeeLVTestCase.dss'
	#FPATH = 'ieee37.clean.reduced.dss'
	#dssConvert.evilGldTreeToDssTree(tree)
	#dssConvert.treeToDss(tree, 'ieeeLVTestCaseNorthAmerican_reduced.dss')

	# Just run DSS
	#runDSS(FPATH)
	# Generate plots, note output is in FPATH dir.
	#voltagePlot(FPATH) # 
	#currentPlot(FPATH)
	#networkPlot(FPATH)
	#THD(FPATH)
	#dynamicPlot(FPATH, 1, 10)
	#faultPlot(FPATH)
	#capacityPlot(FPATH)

	#froots = ['ieee37.clean.dss','ieee123_solarRamp.clean.dss','iowa240.clean.dss','ieeeLVTestCase.clean.dss','ieee8500-unbal_no_fuses.clean.dss']
	#for froot in froots:
	#	froot = froot[:-4]
	#	involts = froot + '_volts.dss'
	#	outvolts = froot + '_mergecontiglines_volts.dss'
	#	rsumm_P, rsumm_D = voltageCompare(involts, outvolts, keep_output=True)

if __name__ == "__main__":
	_tests()
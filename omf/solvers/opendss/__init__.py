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

def qstsPlot(filePath, stepSizeInMinutes, numberOfSteps):
	''' Generate voltage values for a timeseries powerflow. '''
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	volt_coord = runDSS(filePath)
	runDssCommand('Set mode=daily')
	runDssCommand('Set number=1')
	runDssCommand(f'Set stepsize={stepSizeInMinutes}m')
	big_df = pd.DataFrame()
	for step in range(1, numberOfSteps+1):
		runDssCommand('Solve')
		csv_path = f'{dssFileLoc}/volt_prof_hour_{step:04d}.csv'
		runDssCommand(f'Export voltages "{csv_path}"')
		new_data = pd.read_csv(csv_path)
		new_data['Step'] = step
		big_df = pd.concat([big_df, new_data], ignore_index=True)
		os.remove(csv_path)
	big_df.to_csv(f'{dssFileLoc}/voltage_timeseries.csv', index=False)
	# TODO: generate plots.

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
	
def voltageCompare(in1, in2, keep_output=False, outdir='', outfilebase='voltageCompare'):
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
	
	if keep_output:
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

def _mergeContigLinesOnce(tree):
	#TODO refactor this code for performance and readability. O(n^2)=gross.
	
	# Capture the connections to any elements that don't connect to a bus (i.e.monitors, capacitors, meters, generators, etc.)
	busless_objs = [x.get('element','None') for x in tree if 'element' in x]
	
	# Create a lookup table that maps an object's name to its key in the tree (could we just map the name to the tree key...?)
	treeids = range(0,len(tree),1)
	tree = dict(zip(treeids,tree))
	name2key = {tree[i].get('object', None):i for i,v in enumerate(tree)} # note that these are in the form <type>.<name>
	name2key.update({tree[i].get('bus', None):i for i,v in enumerate(tree) if tree[i].get('!CMD', None) == 'setbusxy'}) # form: <name>
	
	 # Destructively iterate through treecopy and perform any modifications on tree.
	treecopy = tree.copy()
	removedids = []
	i_0 = 0
	while treecopy:
		top = treecopy.pop(i_0)
		i_0 = i_0 + 1

		# is this a line object? If not, move to next object in treecopy
		if not top.get('object','None').startswith('line.'):
			continue
		
		# has this item already been removed?
		if top.get('object','None') in removedids:
			continue

		# Get 'to' buses (Could be indicated by 'bus2', or the second, third members of 'buses'. Can assume it will be appended with phase information.)
		busid = ''
		buslist = []
		for k in top.keys():
			if k=='buses':
				buslist = top[k]
				buslist = buslist.replace(']','')
				buslist = buslist.replace('[','')
				buslist = buslist.split(',')
				if len(buslist)>2:
					busid = ''
					continue # more than 2 cnxns = ineligible for reduction
				busid = buslist[1]
			elif k=='bus2':
				busid = top[k]
		if busid == '': # not line-like
			continue 
		bus = tree[name2key[busid.split('.')[0]]]

		# Get ids of objects connected to bus (aka the bottoms)
		bottoms = []
		for k,obj in tree.items():
			objid = obj.get('object','None')
			if obj.get('object', None) == top.get('object', None): # The top cannot also be a bottom
				continue
			if obj.get('!CMD','None')=='setbusxy': # The bus cannot connect to itself
				continue
			allbottoms = []
			for k, v in obj.items(): # See if this object is attached to our bus of interest. If so, capture it.
				if k == 'buses':
					buslist = obj[k]
					buslist = buslist.replace(']','')
					buslist = buslist.replace('[','')
					buslist = buslist.split(',')
					for b in buslist:
						allbottoms.append(b)
				elif k in ['bus','bus1','bus2','element']: # it's a single value
					allbottoms.append(v)
			allbottoms = [x.split('.')[0] for x in allbottoms]
			if ( len([x for x in allbottoms if x == busid.split('.')[0]]) > 0 ): #if any of the bottoms' ids equal the bus id, then obj is connected to our node of interest
				bottoms.append(obj)
		
		# Check for a one-line-in, one-line-out scenario
		if len(bottoms) != 1:
			continue
		bottom = bottoms[0]

		# Is the bottom a line?
		if not bottom.get('object','None').startswith('line.'):
			continue

		# Is the bottom a switch? Let's skip these for now. 
		# TODO: handling for switches when merging them with adjacent line segments is feasible
		if bottom.get('switch','None')=='yes' or bottom.get('switch','None')=='true':
			continue

		# Does the bottom have any monitors, capacitors, energy meters, etc. attached? If so, don't remove it.
		if bottom.get('object','None') in busless_objs:
			continue

		if ('length' in top) and ('length' in bottom):
			# check that the configurations are equal - top/bottom both need to be lines for this to work correctly (i.e. check the intersection between the two sets of properties).
			diffprops = ['!CMD','object','bus1','bus2','length',] # we don't care if these values differ between the top and the bottom
			for k,vt in top.items():
				if not k in diffprops:
					vb = bottom.get(k,'None')
					if vt!=vb:
						break
			
			# Delete bus and bottom; Set top line length = sum of both lines; Connect top to the new bottom.
			toptree = tree[name2key[top['object']]] # modify the tree object directly (this creates a pointer for in-place mods)
			removedids.append(bus['bus'])
			removedids.append(bottom['object'])
			newLen = float(top['length']) + float(bottom['length']) # get the new length
			toptree['length'] = str(newLen)
			toptree['bus2'] = bottom['bus2'] # we know these props exist because we know the top and bottom are lines
			del tree[name2key[bus['bus']]]
			del tree[name2key[bottom['object']]]
	
	with open('removed_ids.txt', 'a') as remfile:
		for remid in removedids:
			remfile.write(remid + '\n')
	return [v for k,v in tree.items()] # back to a list of dicts

def mergeContigLines(tree):
	''' merge all lines that are across nodes and have the same config
	topline --to-> node <-from-- bottomline'''
	removedKeys = 1
	while removedKeys != 0:
		treeKeys = len(tree)
		tree = _mergeContigLinesOnce(tree)
		removedKeys = treeKeys - len(tree)
	return tree

def rollUpLoads(tree):
	
	# Capture the connections to any elements that don't connect to a bus (i.e.monitors, capacitors, meters, generators, etc.)
	#busless_objs = [x.get('element','None') for x in tree if 'element' in x]
	
	# Create a lookup table that maps an object's name to its key in the tree (could we just map the name to the tree key...?)
	treeids = range(0,len(tree),1)
	tree = dict(zip(treeids,tree))
	name2key = {tree[i].get('object', None):i for i,v in enumerate(tree)} # note that these are in the form <type>.<name>
	name2key.update({tree[i].get('bus', None):i for i,v in enumerate(tree) if tree[i].get('!CMD', None) == 'setbusxy'}) # form: <name>
	
	 # Destructively iterate through treecopy and perform any modifications on tree.
	treecopy = tree.copy()
	removedids = []
	i_0 = 0
	while treecopy:
		obj = treecopy.pop(i_0)
		i_0 = i_0 + 1

		# Is this a load object? If not, move to next object in treecopy
		if not obj.get('object','None').startswith('load.'):
			continue
		
		# Has this item already been removed?
		if obj.get('object','None') in removedids:
			continue

		# Get the load's parent bus
		loadparent = obj.get('bus1','None')

		# Get everything else that might be attached to the parent bus
		siblings = []
		for k1,o in tree.items():
			if o.get('object', None) == obj.get('object', None): # Ignore the load's own connection
				continue
			if o.get('!CMD','None')=='setbusxy': # Ignore the bus itself
				continue
			busesofint = []
			for k2,v in o.items(): # See if this object is attached to our bus of interest. If so, capture it.
				if k2 == 'buses':
					buslist = o[k2]
					buslist = buslist.replace(']','')
					buslist = buslist.replace('[','')
					buslist = buslist.split(',')
					for b in buslist:
						busesofint.append(b)
				elif k2 in ['bus','bus1','bus2','element']: # it's a single value
					busesofint.append(v)
			busesofint = [x.split('.')[0] for x in busesofint]
			if ( len([x for x in busesofint if x == loadparent.split('.')[0]]) > 0 ): #if any of the bottoms' ids equal the bus id, then obj is connected to our node of interest
				siblings.append(o)

		# Do the siblings include a transformer? 
		xfmrs = [x for x in siblings if 'transformer' in x.get('object','None')]
		if len(xfmrs)!=1:
			continue
		xfmr = xfmrs[0]
		xfmrbuses = xfmr.get('buses','None') # Note: It is expected that the high side of the transformer is defined first in the 'buses' array
		# TODO: check that the xfrmr connects to a line (fringe case?)

		# Grab sibling loads and ensure there aren't any other element types
		loads = [x for x in siblings if 'load' in x.get('object','None')]
		if len(loads) != len(siblings)-1:
			continue		
		
		# Add current load to siblings. Now the family is complete. (To complete the analogy, this species reproduces asexually and the transformer begot the bus)
		siblings.append(obj)

		# Capture load kws and associate with appropiate %r in a dataframe 
		# (this is an issue right now - how to work with connectivity?)
		# (also, not all situations are arranged bus>xfrmr>bus>loads)
		ldparams = pd.DataFrame(columns=['node','kw','perc_r'])
		for ld in loads:
			kw = ld.get('kw','DNE')
			node = ''
			pass
		kws = [x.get('kw') for x in loads if x.get('kw','DNE')!='DNE']
		
		# Note: We assume that info for the high side (aka the line side) of the xfrmr is in position 0 of the config arrays
		r_arr = xfmr.get('%rs','None')

		# Calculate what the equivalent load should be
		secLoad = 0
		for idx,row in ldparams.iterrows():
			secLoad = secLoad + row['kw']*(1+row['perc_r'])
		#load_eq = (1 + r_prim)*secLoad

		#remove all but one of the loads
		#attach that load to the xfrmr's parent bus
		#remove the loads'parent bus
		#remove xfrmr
		# add to removed id's list
	return


def _tests():
	from dssConvert import dssToTree, distNetViz, evilDssTreeToGldTree, treeToDss
	fpath = ['ieee37.clean.dss','ieee123_solarRamp.clean.dss','iowa240.clean.dss','ieeeLVTestCase.clean.dss','ieee8500-unbal_no_fuses.clean.dss']

	for ckt in fpath:
		
		# Tests for mergeContigLines, voltageCompare, getVoltages, and runDSS
		tree = dssToTree(ckt)
		#gldtree = evilDssTreeToGldTree(tree) # DEBUG
		#distNetViz.viz_mem(gldtree, open_file=True, forceLayout=True) # DEBUG
		oldsz = len(tree)
		tree = mergeContigLines(tree)
		#tree = rollUpLoads(tree)
		newsz = len(tree)
		#gldtree = evilDssTreeToGldTree(tree) # DEBUG
		#distNetViz.viz_mem(gldtree, open_file=True, forceLayout=True) # DEBUG
		outckt_loc = ckt[:-4] + '_mergeContigLines.dss'
		treeToDss(tree, outckt_loc)

		outdir = 'voltageCompare_' + ckt[:-4]
		if not os.path.exists(outdir):
			os.mkdir(outdir)
		involts_loc = ckt[:-4] + '_volts.dss'
		involts = getVoltages(ckt, keep_output=True, outdir=outdir, output_filename=involts_loc)
		outvolts_loc = outckt_loc[:-4] + '_volts.dss'
		outvolts = getVoltages(outckt_loc, keep_output=True, outdir=outdir, output_filename=outvolts_loc)
		#assert voltageCompare(voltpath, voltpath, keep_output=True, output_filename=outpath) <= errorLimit, 'The error between the compared files exceeds the allowable limit of %s%%.'%(errlim*100)
		#assert voltageCompare(voltsdf, voltsdf, keep_output=True, output_filename=outpath) <= errorLimit, 'The error between the compared files exceeds the allowable limit of %s%%.'%(errlim*100)
		#assert voltageCompare(voltpath, voltsdf, keep_output=True, output_filename=outpath) <= errorLimit, 'The error between the compared files exceeds the allowable limit of %s%%.'%(errlim*100)
		rsumm_P, rsumm_D = voltageCompare(involts, outvolts, keep_output=True, outdir=outdir, outfilebase=ckt[:-4])		
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
		print('Objects removed: %s (of %s).\nPercent reduction: %s%%\nMax RMSPE for voltage magnitude: %s%%\nMax RMSPE for voltage angle: %s%%\nMax RMSE for voltage magnitude: %s\nMax RMSE for voltage angle: %s\n'%(oldsz-newsz, oldsz, (oldsz-newsz)*100/oldsz, maxPerrM, maxPerrA, maxDerrM, maxDerrA))
		

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
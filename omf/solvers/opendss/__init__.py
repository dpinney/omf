''' Run OpenDSS and plot the results for arbitrary circuits. '''

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from networkx.algorithms.traversal.depth_first_search import dfs_tree
import math
import os
import warnings
import subprocess
from copy import deepcopy
try:
	import opendssdirect as dss
except:
	warnings.warn('opendssdirect not installed; opendss functionality disabled.')
from omf.solvers.opendss import dssConvert
import omf

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
	runDssCommand('calcvoltagebases')
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

def _getByName(tree, name):
    ''' Return first object with name in tree as an OrderedDict. '''
    matches =[]
    for x in tree:
        if x.get('object',''):
            if x.get('object','').split('.')[1] == name:
                matches.append(x)
    return matches[0]

def newQstsPlot(filePath, stepSizeInMinutes, numberOfSteps, keepAllFiles=False, actions={}, filePrefix='timeseries'):
	''' QSTS with native opendsscmd binary to avoid segfaults in opendssdirect. '''
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	dss_run_file = ''
	dss_run_file += f'redirect {filePath}\n'
	dss_run_file += f'set datapath="{dssFileLoc}"\n'
	dss_run_file += f'set maxcontroliter=1000\n'
	dss_run_file += f'calcvoltagebases\n'
	# Attach Monitors
	tree = dssConvert.dssToTree(filePath)
	mon_names = []
	circ_name = 'NONE'
	base_kvs = pd.DataFrame()
	for ob in tree:
		obData = ob.get('object','NONE.NONE')
		obType, name = obData.split('.')
		mon_name = f'mon{obType}-{name}'
		if obData.startswith('circuit.'):
			circ_name = name
		elif obData.startswith('vsource.'):
			dss_run_file += f'new object=monitor.{mon_name} element={obType}.{name} terminal=1 mode=0\n'
			mon_names.append(mon_name)
		elif obData.startswith('isource.'):
			dss_run_file += f'new object=monitor.{mon_name} element={obType}.{name} terminal=1 mode=0\n'
			mon_names.append(mon_name)
		elif obData.startswith('generator.') or obData.startswith('isource.') or obData.startswith('storage.') or obData.startswith('pvsystem.'):
			mon_name = f'mongenerator-{name}'
			dss_run_file += f'new object=monitor.{mon_name} element={obType}.{name} terminal=1 mode=1 ppolar=no\n'
			mon_names.append(mon_name)
		elif ob.get('object','').startswith('load.'):
			dss_run_file += f'new object=monitor.{mon_name} element={obType}.{name} terminal=1 mode=0\n'
			mon_names.append(mon_name)
			new_kv = pd.DataFrame({'kv':[float(ob.get('kv',1.0))],'Name':['monload-' + name]})
			base_kvs = base_kvs.append(new_kv)
		elif ob.get('object','').startswith('capacitor.'):
			dss_run_file += f'new object=monitor.{mon_name} element={obType}.{name} terminal=1 mode=6\n'
			mon_names.append(mon_name)
		elif ob.get('object','').startswith('regcontrol.'):
			tformer = ob.get('transformer','NONE')
			winding = ob.get('winding',1)
			dss_run_file += f'new object=monitor.{mon_name} element=transformer.{tformer} terminal={winding} mode=2\n'
			mon_names.append(mon_name)
	# Run DSS
	dss_run_file += f'set mode=yearly stepsize={stepSizeInMinutes}m \n'
	if actions == {}:
		# Run all steps directly.
		dss_run_file += f'set number={numberOfSteps}\n'
		dss_run_file += 'solve\n'
	else:
		# Actions defined, run them at the appropriate timestep.
		dss_run_file += f'set number=1\n'
		for step in range(1, numberOfSteps+1):
			action = actions.get(step)
			if action != None:
				print(f'Step {step} executing:', action)
				dss_run_file += action
			dss_run_file += 'solve\n'
	# Export all monitors
	for name in mon_names:
		dss_run_file += f'export monitors monitorname={name}\n'
	# Write runner file and run.
	with open(f'{dssFileLoc}/dss_run_file.dss', 'w') as run_file:
		run_file.write(dss_run_file)
	# Run in the right directory and suppress the output
	subprocess.run('opendsscmd dss_run_file.dss', cwd=dssFileLoc, shell=True, check=True, stdout=subprocess.DEVNULL)
	# Aggregate monitors
	all_gen_df = pd.DataFrame()
	all_load_df = pd.DataFrame()
	all_source_df = pd.DataFrame()
	all_control_df = pd.DataFrame()
	for name in mon_names:
		csv_path = f'{dssFileLoc}/{circ_name}_Mon_{name}_1.csv'
		df = pd.read_csv(f'{circ_name}_Mon_{name}_1.csv')
		if name.startswith('monload-'):
			# reassign V1 single phase voltages outputted by DSS to the appropriate column and filling Nans for neutral phases (V2)
			# three phase print out should work fine as is
			ob_name = name.split('-')[1]
			# print("ob_name:", ob_name)
			the_object = _getByName(tree, ob_name)
			# print("the_object:", the_object)
			# create phase list, removing neutral phases
			phase_ids = the_object.get('bus1','').replace('.0','').split('.')[1:]
			# print("phase_ids:", phase_ids)
			# print("headings list:", df.columns)
			if phase_ids == ['1']:
				df[[' V2']] = np.NaN
				df[[' V3']] = np.NaN
			elif phase_ids == ['2']:
				df[[' V2']] = df[[' V1']]
				df[[' V1']] = np.NaN
				df[[' V3']] = np.NaN
			elif phase_ids == ['3']:
				df[[' V3']] = df[[' V1']]
				df[[' V1']] = np.NaN
				df[[' V2']] = np.NaN
			# # print("df after phase reassignment:")
			# # print(df.head(10))
			df['Name'] = name
			all_load_df = pd.concat([all_load_df, df], ignore_index=True, sort=False)
			#pd.set_option('display.max_columns', None)
			# print("all_load_df:", df.head(50))
		elif name.startswith('mongenerator-'):
			# reassign V1 single phase voltages outputted by DSS to the appropriate column and filling Nans for neutral phases (V2)
			# three phase print out should work fine as is
			ob_name = name.split('-')[1]
			# print("ob_name:", ob_name)
			the_object = _getByName(tree, ob_name)
			# print("the_object:", the_object)
			# create phase list, removing neutral phases
			phase_ids = the_object.get('bus1','').replace('.0','').split('.')[1:]
			# print("phase_ids:", phase_ids)
			# print("headings list:", df.columns)
			if phase_ids == ['1']:
				df[[' P2 (kW)']] = np.NaN
				df[[' P3 (kW)']] = np.NaN
			elif phase_ids == ['2']:
				df[[' P2 (kW)']] = df[[' P1 (kW)']]
				df[[' P1 (kW)']] = np.NaN
				df[[' P3 (kW)']] = np.NaN
			elif phase_ids == ['3']:
				df[[' P3 (kW)']] = df[[' P1 (kW)']]
				df[[' P1 (kW)']] = np.NaN
				df[[' P2 (kW)']] = np.NaN
			# # print("df after phase reassignment:")
			# # print(df.head(10))
			df['Name'] = name
			all_gen_df = pd.concat([all_gen_df, df], ignore_index=True, sort=False)
		elif name.startswith('monvsource-'):
			df['Name'] = name
			all_source_df = pd.concat([all_source_df, df], ignore_index=True, sort=False)
		elif name.startswith('monisource-'):
			df['Name'] = name
			all_source_df = pd.concat([all_source_df, df], ignore_index=True, sort=False)
		elif name.startswith('moncapacitor-'):
			df['Type'] = 'Capacitor'
			df['Name'] = name
			df = df.rename({' Step_1 ': 'Tap(pu)'}, axis='columns') #HACK: rename to match regulator tap name
			all_control_df = pd.concat([all_control_df, df], ignore_index=True, sort=False)
		elif name.startswith('monregcontrol-'):
			df['Type'] = 'Transformer'
			df['Name'] = name
			df = df.rename({' Tap (pu)': 'Tap(pu)'}, axis='columns') #HACK: rename to match cap tap name
			all_control_df = pd.concat([all_control_df, df], ignore_index=True, sort=False)
		if not keepAllFiles:
			os.remove(csv_path)
	# Collect switching actions
	for key, ob in actions.items():
		if ob.startswith('open'):
			switch_ob = ob.split()
			ob_name = switch_ob[1][7:]
			new_row = {'hour':key, 't(sec)':0.0,'Tap(pu)':1,'Type':'Switch','Name':ob_name}
			all_control_df = all_control_df.append(new_row, ignore_index=True)
	for key, ob in actions.items():
		if ob.startswith('close'):
			switch_ob = ob.split()
			ob_name = switch_ob[1][7:]
			new_row = {'hour':key, 't(sec)':0.0,'Tap(pu)':1,'Type':'Switch','Name':ob_name}
			all_control_df = all_control_df.append(new_row, ignore_index=True)
	# Write final aggregates
	if not all_gen_df.empty:
		all_gen_df.sort_values(['Name','hour'], inplace=True)
		all_gen_df.columns = all_gen_df.columns.str.replace(r'[ "]','',regex=True)
		all_gen_df.to_csv(f'{dssFileLoc}/{filePrefix}_gen.csv', index=False)
	if not all_control_df.empty:
		all_control_df.sort_values(['Name','hour'], inplace=True)
		all_control_df.columns = all_control_df.columns.str.replace(r'[ "]','',regex=True)
		all_control_df.to_csv(f'{dssFileLoc}/{filePrefix}_control.csv', index=False)
	if not all_source_df.empty:
		all_source_df.sort_values(['Name','hour'], inplace=True)
		all_source_df.columns = all_source_df.columns.str.replace(r'[ "]','',regex=True)
		all_source_df["P1(kW)"] = all_source_df["V1"].astype(float) * all_source_df["I1"].astype(float) / 1000.0
		all_source_df["P2(kW)"] = all_source_df["V2"].astype(float) * all_source_df["I2"].astype(float) / 1000.0
		all_source_df["P3(kW)"] = all_source_df["V3"].astype(float) * all_source_df["I3"].astype(float) / 1000.0
		all_source_df.to_csv(f'{dssFileLoc}/{filePrefix}_source.csv', index=False)
	if not all_load_df.empty:
		all_load_df.sort_values(['Name','hour'], inplace=True)
		all_load_df.columns = all_load_df.columns.str.replace(r'[ "]','',regex=True)
		all_load_df = all_load_df.join(base_kvs.set_index('Name'), on='Name')
		# TODO: insert ANSI bands here based on base_kv?  How to not display two bands per load with the appended CSV format?
		all_load_df['V1(PU)'] = all_load_df['V1'].astype(float) / (all_load_df['kv'].astype(float) * 1000.0)
		# HACK: reassigning 0V to "NaN" as below does not removes 0V phases but could impact 2 phase systems
		#all_load_df['V2'][(all_load_df['VAngle2']==0) & (all_load_df['V2']==0)] = "NaN"
		all_load_df['V2(PU)'] = all_load_df['V2'].astype(float) / (all_load_df['kv'].astype(float) * 1000.0)
		all_load_df['V3(PU)'] = all_load_df['V3'].astype(float) / (all_load_df['kv'].astype(float) * 1000.0)
		all_load_df.to_csv(f'{dssFileLoc}/{filePrefix}_load.csv', index=False)

def hosting_capacity(FNAME:str, GEN_BUSES:list, STEPS:int, KW:float):
	''' Using DSS circuit at FNAME, add KW sized generators at each of the GEN_BUSES up to STEPS times.
		Returns two values:
			a dataframe with max per-phase voltages after each addition, and
			the kW addition that pushed voltages over the limit.
	'''
	# Derived constants.
	fullpath = os.path.abspath(FNAME)
	filedir = os.path.dirname(fullpath)
	volt_file = f'{filedir}/volts.csv'
	ansi_a_max_pu = 1.05
	ansi_b_max_pu = 1.058
	DEFAULT_KV = 2.14
	tree = dssConvert.dssToTree(fullpath)
	# Find the insertion kv levels.
	kv_mappings = get_bus_kv_mappings(fullpath)
	for bus in GEN_BUSES:
		if bus not in kv_mappings:
			warnings.warn(f'Voltage unkown for {bus}, defaulting to {DEFAULT_KV}')
	# Get insertion bus; should always be safe to insert above makebuslist.
	for i, ob in enumerate(tree):
		if ob.get('!CMD', None) == 'makebuslist':
			insertion_index = i
	max_kw = 0.0
	buses_with_cap_left = {}
	results = [['kw_add', 'v_max_pu1', 'v_max_pu2', 'v_max_pu3', 'v_max_all_pu']]
	for step in [0] + list(range(1, STEPS + 1)):
		new_tree = deepcopy(tree)
		# Insert generators.
		gen_template = {
			'!CMD': 'new',
			'object': None,
			'bus1': None,
			'kw': KW * step,
			'pf': '1.0',
			'conn': 'wye',
			'phases': '3',
			'kv': None,
			'model': '1' }
		for bus in GEN_BUSES:
			if step != 0: # skip generation adding for baseline
				new_gen = dict(gen_template)
				new_gen['object'] = f'generator.hostcap_{bus}'
				new_gen['bus1'] = f'{bus}.1.2.3'
				new_gen['kv'] = kv_mappings.get(bus, DEFAULT_KV)
				new_tree.insert(insertion_index, new_gen)
		# Calc voltages.
		dssConvert.treeToDss(new_tree, 'HOSTCAP.dss')
		voltagePlot('HOSTCAP.dss')
		df = pd.read_csv(volt_file)
		v_max_pu1, v_max_pu2, v_max_pu3 =  df[' pu1'].max(), df[' pu2'].max(), df[' pu2'].max()
		v_max_pu_all = max(v_max_pu1, v_max_pu2, v_max_pu3)
		results.append([KW * step, v_max_pu1, v_max_pu2, v_max_pu3, v_max_pu_all])
		# Determine which buses still have capacity
		if v_max_pu_all > ansi_b_max_pu:
			max_kw = KW * max(step - 1, 0)
			df = pd.DataFrame(results[1:], columns=results[0])
			return df, max_kw
	df = pd.DataFrame(results[1:], columns=results[0])
	return df, max_kw

def hosting_capacity_max(FNAME, GEN_BUSES, STEPS, KW):
	''' Keep calculating hosting capacity, uniformly distributing generation, dropping the lowest capacity bus each time.
		Gives a decent estimate of the amount of hosting capacity at each gen_bus when deploying generation on all of them.
	'''
	results = {}
	prev_max = 0
	DEFAULT_KV = 2.14
	fullpath = os.path.abspath(FNAME)
	for i in range(len(GEN_BUSES) - 1):
		# Run uniform hosting capacity.
		df, max_kw = hosting_capacity(FNAME, GEN_BUSES, STEPS, KW)
		# print('RUNNING ON', GEN_BUSES)
		# print(df)
		# print(max_kw)
		prev_max = prev_max + max_kw
		# Update the file with new max generators.
		tree = dssConvert.dssToTree(FNAME)
		kv_mappings = get_bus_kv_mappings(fullpath)
		for j, ob in enumerate(tree):
			if ob.get('!CMD', None) == 'makebuslist':
				insertion_index = j
		for bus in GEN_BUSES:
			gen = {
				'!CMD': 'new',
				'object': f'generator.hostcap_{bus}_{i}_old',
				'bus1': f'{bus}.1.2.3',
				'kw': max_kw,
				'pf': '1.0',
				'conn': 'wye',
				'phases': '3',
				'kv': kv_mappings.get(bus, DEFAULT_KV),
				'model': '1' }
			tree.insert(insertion_index, gen)
		dssConvert.treeToDss(tree, f'HOSTCAP_{i}.dss')
		FNAME = f'HOSTCAP_{i}.dss'
		# Individual caps left.
		cap_left = {}
		for bus in GEN_BUSES:
			df, ind_max_kw = hosting_capacity(FNAME, [bus], STEPS, KW)
			cap_left[bus] = ind_max_kw
		# print(cap_left)
		# Drop zeroes and lowest
		cap_rem_pairs = list(cap_left.items())
		cap_rem_pairs.sort(key=lambda x:x[1])
		removes = [x for x in cap_rem_pairs if x[1] == 0.0]
		if len(removes) == 0:
			# no zeroes so drop lowest
			min_cap = cap_rem_pairs[0][0]
			cap_added = cap_rem_pairs[0][1]
			removes.append((min_cap,cap_added))
		# print('REMOVES',removes)
		if len(removes) > 0:
			for bus, ignore in removes:
				results[bus] = prev_max
				GEN_BUSES.remove(bus)
		if len(GEN_BUSES) < 2:
			return results
	return results

def get_obj_by_name(name, tree, cmd=None):
	''' Get object with given name in tree. If multiple or zero objs found, raise exceptions. '''
	all_obs_name = [x for x in tree if x.get('object','').endswith(f'.{name}')]
	if cmd:
		all_obs_name = [x for x in all_obs_name if x.get('!CMD','') == cmd]
	num_found = len(all_obs_name)
	if num_found == 1:
		return all_obs_name[0]
	elif num_found == 0:
		err = f'No object with name "{name}" found.'
		raise Exception(err)
	else:
		err = f'Multiple objects with given name found: {all_obs_name}'
		raise Exception(err)

def get_subtree_obs(line, tree):
	''' Get all objects down-line from the affected line. '''
	aff_ob = get_obj_by_name(line, tree, cmd='new')
	aff_bus = aff_ob.get('bus2').split('.')[0]
	net = dssConvert.dss_to_networkx(None, tree=tree)
	sub_tree = dfs_tree(net, aff_bus)
	sub_names = [x for x in sub_tree.nodes]
	sub_obs = [x for x in tree if x.get('object','NO.NO').split('.')[1] in sub_names]
	return sub_obs

def voltagePlot(filePath, PU=True):
	''' Voltage plotting routine. Creates 'voltages.csv' and 'Voltage [PU|V].png' in directory of input file.'''
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	volt_coord = runDSS(filePath)
	runDssCommand('Export voltages "' + dssFileLoc + '/volts.csv"')
	voltageDF = pd.read_csv(dssFileLoc + '/volts.csv')
	plt.title('Voltage Profile')
	plt.ylabel('Count')
	if PU:
		for i in range(1, 4): 
			volt_ind = ' pu' + str(i)
			plt.hist(voltageDF[volt_ind], label='Phase ' + str(i))
		plt.xlabel('Voltage [PU]')
		plt.legend()
		plt.savefig(dssFileLoc + '/Voltage Profile [PU].png')
	else:
		# plt.axis([1, 7, 2000, 3000]) # Ignore sourcebus-much greater-for overall magnitude.
		for i in range(1, 4): 
			mag_ind = ' Magnitude' + str(i)
			plt.hist(voltageDF[mag_ind], label='Phase ' + str(i))
		plt.xlabel('Voltage [V]')
		plt.legend()
		plt.savefig(dssFileLoc + '/Voltage Profile [V].png')
	plt.clf()

def get_bus_kv_mappings(path_to_dss):
	''' Returns a map {bus_name:base_kv} where base_kv is the line-to-neutral voltage.'''
	voltagePlot(path_to_dss)
	file_loc = os.path.dirname(os.path.abspath(path_to_dss))
	volt_file_loc = f'{file_loc}/volts.csv'
	volt_df = pd.read_csv(volt_file_loc)
	volt_df['kv_ln'] = volt_df[' BasekV']/math.sqrt(3)
	out_data = volt_df[['Bus','kv_ln']].values.tolist()
	out_dict = {x[0].lower():x[1] for x in out_data}
	return out_dict

def get_bus_phasing_map(path_to_dss):
	''' Returns a map {bus_name:phase_list} where phase list a list of all powered phases (e.g. [1,3]).'''
	voltagePlot(path_to_dss)
	path_to_dss = os.path.abspath(path_to_dss)
	file_loc = os.path.dirname(path_to_dss)
	volt_file_loc = f'{file_loc}/volts.csv'
	volt_df = pd.read_csv(volt_file_loc).set_index('Bus')
	bus_df = volt_df.transpose()
	results = {bus:[] for bus in bus_df.columns}
	for bus in bus_df.columns:
		for i, pu in enumerate([' pu1', ' pu2', ' pu3']):
			if bus_df[bus][pu] > 0:
				results[bus].append(i + 1)
	return results

def currentPlot(filePath):
	''' Current plotting function.'''
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	curr_coord = runDSS(filePath)
	runDssCommand('Export currents "' + dssFileLoc + '/currents.csv"')
	currentDF = pd.read_csv(dssFileLoc + '/currents.csv')
	plt.xlabel('Current [A]')
	plt.ylabel('Count')
	plt.title('Current Profile')
	for i in range(1, 3):
		for j in range(1, 4):
			cur_ind = ' I' + str(i) + '_' + str(j)
			plt.hist(currentDF[cur_ind], label=cur_ind)
	plt.legend()
	plt.savefig(dssFileLoc + '/Current Profile.png')
	plt.clf()

def networkPlot(filePath, figsize=(20,20), output_name='networkPlot.png', show_labels=True, node_size=300, font_size=8):
	''' Plot the physical topology of the circuit.
	Returns a networkx graph of the circuit as a bonus. '''
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
		pos[bus_name] = (float(row['X']), float(row['Y']))
	# Get the connecting edges using Pandas.
	lines = dss.utils.lines_to_dataframe()
	edges = []
	for index, row in lines.iterrows():
		#HACK: dss upercases everything in the coordinate output.
		bus1 = row['Bus1'].split('.')[0].upper()
		bus2 = row['Bus2'].split('.')[0].upper()
		edges.append((bus1, bus2))
	G.add_edges_from(edges)
	# Remove buses withouts coords
	no_pos_nodes = set(G.nodes()) - set(pos)
	if len(no_pos_nodes) > 0:
		warnings.warn(f'Node positions missing for {no_pos_nodes}')
	G.remove_nodes_from(list(no_pos_nodes))
	# We'll color the nodes according to voltage.
	volt_values = {}
	labels = {}
	for index, row in volts.iterrows():
		if row['Bus'].upper() in [x.upper() for x in pos]:
			volt_values[row['Bus']] = row[' pu1']
			labels[row['Bus']] = row['Bus']
	colorCode = [volt_values.get(node, 0.0) for node in G.nodes()]
	# Start drawing.
	plt.figure(figsize=figsize) 
	nodes = nx.draw_networkx_nodes(G, pos, node_color=colorCode, node_size=node_size)
	edges = nx.draw_networkx_edges(G, pos)
	if show_labels:
		nx.draw_networkx_labels(G, pos, labels, font_size=font_size)
	plt.colorbar(nodes)
	plt.legend()
	plt.title('Network Voltage Layout')
	plt.tight_layout()
	plt.savefig(dssFileLoc + '/' + output_name)
	plt.clf()
	return G

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
	# for index, row in voltHarmonics.iterrows():
	voltHarmonics['THD'] = (voltHarmonics[' Magnitude1'] + voltHarmonics[' Magnitude2'] + voltHarmonics[' Magnitude3'])/3
	plt.hist(voltHarmonics['THD'])
	plt.xlabel('THD [Avg%]')
	plt.ylabel('Count')
	plt.title('Total Harmonic Distortion')
	plt.savefig(dssFileLoc + '/THD.png')
	plt.clf()

def dynamicPlot(filePath, time_step_s=0.001, iterations=100, at_elem='Vsource.SOURCE'):
	''' Do a dynamic, long-term study of the powerflow. time_step is in seconds. '''
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))	
	runDSS(filePath)
	runDssCommand(f'new object=monitor.dynamic_monitor element={at_elem}')
	runDssCommand('solve')
	runDssCommand(f'solve mode=dynamics stepsize={time_step_s} number={iterations}')
	runDssCommand('export monitor dynamic_monitor filename=dynamic_monitor.csv')
	circ_name = dss.Circuit.Name()
	allDF = pd.read_csv(f'{dssFileLoc}/{circ_name}_Mon_dynamic_monitor.csv')
	fig, axs = plt.subplots(2)
	for vname in [' V1',' V2',' V3']:
		axs[0].plot(allDF[vname], label=vname)
	for cname in [' I1',' I2',' I3']:
		axs[1].plot(allDF[cname], label=cname)
	# # plt.xticks(range(iterations), [time_step_s * x for x in range(iterations)])
	axs[0].set_xlabel('Time [step]')
	axs[1].set_xlabel('Time [step]')
	axs[0].set_ylabel('Voltage [V]')
	axs[1].set_ylabel('Current [A]')
	axs[0].legend()
	fig.suptitle(f'Dynamic Simulation at {at_elem}')
	fig.tight_layout()
	fig.savefig(dssFileLoc + '/DynamicPowerPlot.png')

def faultPlot(filePath, faultCommand):
	''' Plot fault study for filePath dss and faultCommand (valid opendss fault str) ''' 
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	runDSS(filePath)
	runDssCommand(faultCommand)
	runDssCommand('Solve Mode=FaultStudy')
	runDssCommand('Export fault "' + dssFileLoc + '/faults.csv"')
	faultDF = pd.read_csv(dssFileLoc + '/faults.csv')
	faultDF.columns = faultDF.columns.str.strip()
	plt.xlabel('Bus Index')
	plt.ylabel('Current [Amps]')
	plt.yscale('log')
	plt.title('Fault Study')
	xpos = [x*4 for x in range(len(faultDF['Bus']))]
	plt.bar(xpos, faultDF['1-Phase'], label='1-Phase to Ground [A]')
	plt.bar([x+1 for x in xpos], faultDF['3-Phase'], label='3-Phase to Ground [A]')
	plt.bar([x+2 for x in xpos], faultDF['L-L'], label='Line-to-Line [A]')
	plt.xticks([x+1 for x in xpos], [int(x/4) for x in xpos])
	plt.legend(loc='upper center')
	plt.savefig(dssFileLoc + '/Fault Currents.png')
	plt.clf()

def capacityPlot(filePath):
	''' Plot power vs. distance '''
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	coords = runDSS(filePath)
	runDssCommand('Export Capacity "' + dssFileLoc + '/capacity.csv"')
	capacityDF = pd.read_csv(dssFileLoc + '/capacity.csv')
	plt.title('Transformer Loading')
	plt.ylabel('Loading Normal Rating [%]')
	plt.xlabel('Component Index')
	# print(capacityDF)
	x = capacityDF['Name']
	x_pos = range(len(x))
	plt.bar(
		x_pos,
		capacityDF[' %normal'],
		color='red'
	)
	plt.tight_layout() # Otherwise the right y-label is slightly clipped
	# plt.xticks(x_pos, x) # Doesn't fit. Names too long.
	# plt.legend()
	plt.savefig(dssFileLoc + '/Capacity Profile.png')
	plt.clf()
	
def voltageCompare(in1, in2, saveascsv=False, with_plots=False, outdir='', outfilebase='voltageCompare'):
	'''Compares two instances of the information provided by the 'Export voltages' opendss command and outputs 
	the maximum error ([0,100]% and absolute difference in [-inf,inf] volts or [-180,180] degrees) encountered for any value compared. If the 'keep_output' flag is set to 'True', also 
	outputs a file that describes the maximum, average, and minimum error encountered for each column. Use the 
	'output_filename' parameter to set the output file name. Inputs can be formatted as a .dss file of voltages
	output by OpenDSS, or as a dataframe of voltages obtained using the OMF's getVoltages().'''
	#TODO: rewrite description
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
	# merge bvolts into avolts
	cols = bvolts.columns
	bvolts.columns = ["b_" + x for x in cols]
	ins = avolts.join(bvolts)
	del avolts
	del bvolts
	ins = ins.dropna()
	cols = [c for c in cols if (not c.startswith(' pu')) and (not c.startswith(' Node'))]
	colsP = [c + ' (0-100%)' for c in cols]
	colsD = []
	for c in cols:
		if c.lower().startswith(' basekv'):
			colsD.append(c + ' (kV)')
		if c.lower().startswith(' magnitude'):
			colsD.append(c + ' (V)')
		if c.lower().startswith(' angle'):
			colsD.append(c + ' (deg)')

	resultErrD = pd.DataFrame(index=ins.index, columns=colsD)
	resultErrP = pd.DataFrame(index=ins.index, columns=colsP)

	for i, col in enumerate(cols):
		for row in ins.index:
			ina = ins.loc[row,col]
			inb = ins.loc[row,"b_" + col]
			resultErrP.loc[row,colsP[i]] = 100*(ina - inb)/ina if ina!=0 else 0
			resultErrD.loc[row,colsD[i]] = ina - inb
	# Construct results
	resultSummP = pd.DataFrame(index=['Max %Err', 'Avg %Err', 'Min %Err', 'RMSPE'], columns=colsP)
	resultSummD = pd.DataFrame(index=['Max Diff', 'Avg Diff', 'Min Diff', 'RMSE'], columns=colsD)
	for cp in colsP:
		resultSummP.loc['Max %Err',cp] = resultErrP.loc[:,cp].max(skipna=True)
		resultSummP.loc['Avg %Err',cp] = resultErrP.loc[:,cp].mean(skipna=True)
		resultSummP.loc['Min %Err',cp] = resultErrP.loc[:,cp].min(skipna=True)
		resultSummP.loc['RMSPE',cp] = math.sqrt((resultErrP.loc[:,cp]**2).mean())
	for cd in colsD:
		resultSummD.loc['Max Diff',cd] = resultErrD.loc[:,cd].max(skipna=True)
		resultSummD.loc['Avg Diff',cd] = resultErrD.loc[:,cd].mean(skipna=True)
		resultSummD.loc['Min Diff',cd] = resultErrD.loc[:,cd].min(skipna=True)
		resultSummD.loc['RMSE',cd] = math.sqrt((resultErrD.loc[:,cd]**2).mean())
	if saveascsv:
		outroot = outdir + '/' + outfilebase

		resultErrP.dropna(inplace=True)
		resultSummP.to_csv(outroot + '_Perc.csv', header=True, index=True, mode='w')
		emptylineP = pd.DataFrame(index=[''],columns=colsP)
		emptylineP.to_csv(outroot + '_Perc.csv', header=False, index=True, mode='a')
		resultErrP.to_csv(outroot + '_Perc.csv', header=True, index=True, mode='a')
		
		resultErrD.dropna(inplace=True)
		resultSummD.to_csv(outroot + '_Diff.csv', header=True, index=True, mode='w')
		emptylineD = pd.DataFrame(index=[''],columns=colsD)
		emptylineD.to_csv(outroot + '_Diff.csv', header=False, index=True, mode='a')
		resultErrD.to_csv(outroot + '_Diff.csv', header=True, index=True, mode='a')
	if with_plots:
		# Produce boxplots to visually analyze the residuals
		from matplotlib.pyplot import boxplot
		magcols = [c for c in colsD if c.lower().startswith(' magnitude')]
		bxpltMdf = pd.DataFrame(index=ins.index,data=resultErrD,columns=magcols)
		bxpltM = []
		for item in magcols:
			bxpltM.append(bxpltMdf[item])
		figM, axM = plt.subplots()
		axM.set_title('Boxplot of Residuals: Voltage Magnitude (V)')
		plt.xticks(rotation=45)
		axM.set_xticklabels(magcols)
		axM.boxplot(bxpltM)
		figM.savefig(outroot + '_boxplot_Mag.png', bbox_inches='tight')
		plt.close()
		angcols = [c for c in colsD if c.lower().startswith(' angle')]
		bxpltAdf = pd.DataFrame(data=resultErrD[angcols],columns=angcols)
		bxpltA = []
		for item in angcols:
			bxpltA.append(bxpltAdf[item])
		figA, axA = plt.subplots()
		axA.set_title('Boxplot of Residuals: Voltage Angle (deg)')
		plt.xticks(rotation=45)
		axA.set_xticklabels(angcols)
		axA.boxplot(bxpltA)
		figA.savefig(outroot + '_boxplot_Ang.png', bbox_inches='tight')
		plt.close()
		for i,c in enumerate(cols):
			# construct a dataframe of busname, input, output, and residual
			dat = pd.concat([ins[c],ins['b_' + c],resultErrP[colsP[i]],resultErrD[colsD[i]]], axis=1,join='inner')
			dat.columns = ['buses+','buses-','residuals_P','residuals_D'] # buses+ denotes the value (voltage or angle) of the circuit with more buses; buses- denotes that of the circuit with fewer
			dat = dat.sort_values(by=['buses-','buses+'], ascending=True, na_position='first')
			# Produce plot of residuals
			#pltlenR = math.ceil(len(dat['residuals_P'])/2)
			#figR, axR = plt.subplots(figsize=(pltlenR,12))
			#axR.plot(dat['buses-'], 'k.', alpha=0.15)
			figR, axR = plt.subplots()
			axR.plot(dat['buses-'], dat['residuals_D'], 'k.', alpha=0.15)
			axR.set_title('Plot of Residuals: ' + colsD[i])
			#plt.xticks(rotation=45)
			axR.set_xlabel('Value for circuit with fewer buses: ' + colsD[i])
			axR.set_ylabel('Value of Residual')
			figR.savefig(outroot + '_residualplot_' + colsD[i] +'_.png', bbox_inches='tight')
			plt.close()
			# Produce scatter plots
			figS, axS = plt.subplots()
			axS.set_title('Scatter Plot: ' + colsD[i])
			axS.plot(dat['buses-'], dat['buses+'], 'k.', alpha=0.15)
			axS.set_xlabel('Value of ' + colsD[i] + ' for circuit with fewer buses')
			axS.set_ylabel('Value of ' + colsD[i] + ' for circuit with more buses')
			figS.savefig(outroot + '_scatterplot_' + colsD[i] +'_.png', bbox_inches='tight')
			plt.close()
	return resultSummP, resultSummD

def getVoltages(dssFilePath, keep_output=False, outdir='', output_filename='voltages.csv'):
	# TODO: rename to voltageGet for consistency with other functions?
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

def reduceCircuit(tree):
	tree = mergeContigLines(tree)
	tree = rollUpTriplex(tree)
	tree = rollUpLoadTransformer(tree)
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
		# Is the top a switch? Let's skip these for now. 
		# TODO: handle switches when merging them with adjacent line segments
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
		# Is the bottom a switch? Let's skip these for now. 
		# TODO: handle switches when merging them with adjacent line segments
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

def rollUpTriplex(tree):
	'''Remove a triplex line and capture losses in the load it serves by applying enineerging estimates. Applies 
	to instances where one or more loads are connected to a single bus, and that bus is connected to a line which
	is then connected to a transformer.'''
	# Applicable circuit model: [one or more loads]-[bus]-[line]-[bus]-[transformer]-...
	tree = applyCnxns(tree)
	from copy import deepcopy
	from math import sqrt
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
		# Get the load's parent bus
		loadbusid = obj.get('bus1','None').split('.')[0]
		loadbus = treecopy[name2key[loadbusid]]
		# Has this loadbus already been removed? if so, move on to the next object in treecopy
		if loadbusid in removedids:
			continue
		# Get everything that is attached to the parent bus
		loadsiblings = loadbus.get('!CNXNS','None')
		loadsiblings = loadsiblings.replace('[','').replace(']','')
		loadsiblings = loadsiblings.split(',')
		# Does the load's bus connect to a single line? If not, move to next object in treecopy
		loads = [x for x in loadsiblings if x.startswith('load.')]
		if len(loadsiblings)-len(loads) != 1:
			continue
		lines = [x for x in loadsiblings if x.startswith('line.')]
		if len(lines) != 1:
			continue
		# Capture the line for later removal
		linetoremove = lines[0]
		# Get the line's parent bus. 
		linebusid = treecopy[name2key[linetoremove]].get('bus1','None').split('.')[0] # bus1='from'; bus2='to'
		linebus = treecopy[name2key[linebusid]]
		# Get everything connected to the linebus
		linesiblings = linebus.get('!CNXNS','None')
		linesiblings = linesiblings.replace('[','').replace(']','')
		linesiblings = linesiblings.split(',')
		# Does the line's bus connect to one transformer? If not, move to next object in treecopy
		xfrmrids = [x for x in linesiblings if x.startswith('transformer.')]
		if len(linesiblings)-len(xfrmrids) != 1:
			continue		
		xfrmrids = list(set(xfrmrids)) # 3-winding xfrmrs often define two connections to the same bus (i.e. split-phase connections)
		if len(xfrmrids) != 1:
			continue
		#everything checks out. Begin modifications.
		# Fix the loads' and linebus' connections and correct kw for losses associated with removed triplex line 
		for load in loads:
			# Set linebus as loads' parent
			load_obj = tree[name2key[load]]
			conncode = load_obj.get('bus1','').split('.',1)[1]
			load_obj['bus1'] = linebusid + '.' + conncode
			# Check number of connections and fix load kw and kv values to capture triplex losses (0.81%)
			conncode = conncode.split('.')
			if '0' in conncode:
				conncode.remove('0') # no losses for grounds.
			load_obj['kw'] = str(float(load_obj.get('kw','0')) * 1.0081)
			#note: Corrections to power factor are negligible because triplex lines are short.
			tree[name2key[load]] = load_obj
			# Add load to linebus connections
			linebus_obj = tree[name2key[linebusid]]
			linebuscons = linebus_obj.get('!CNXNS','None')
			linebuscons = linebuscons.replace('[','').replace(']','')
			linebuscons = linebuscons.split(',')
			if linetoremove in linebuscons:
				linebuscons.remove(linetoremove)
			cstr = '['
			for elm in linebuscons:
				cstr += elm + ','
			cstr += load
			cstr = cstr + ']'
			linebus_obj['!CNXNS'] = cstr
			tree[name2key[linebusid]] = linebus_obj
		# Remove the line and loadbus (if not already removed)
		removedids.append(linetoremove)
		del tree[name2key[linetoremove]]
		removedids.append(loadbusid)
		del tree[name2key[loadbusid]]
	tree = [v for k,v in tree.items()] # back to a list of dicts
	tree = removeCnxns(tree)
	if os.path.exists('removed_ids.txt'):
		os.remove('removed_ids.txt')
	with open('removed_ids.txt', 'a') as remfile:
		for remid in removedids:
			remfile.write(remid + '\n')
	return tree

def rollUpLoadTransformer(tree, combine_loads=True):
	'''Removes a load-serving transformer and captures its losses in the loads it serves by applying 
	an engineering estimate. This process also combines multiple loads into a single representative load. Applies to instances where one or more loads are connected to a 
	single bus, and that bus is connected to a transformer which is connected to a bus.'''
	# Applicable circuit model: [one or more loads]-[bus]-[transformer]-[bus]...
	tree = applyCnxns(tree)
	from copy import deepcopy
	from math import sqrt
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
		# Get the load's parent bus
		loadbusid = obj.get('bus1','None').split('.')[0]
		loadbus_obj = treecopy[name2key[loadbusid]]
		# Has this loadbus already been removed? if so, move on to the next object in treecopy
		if loadbusid in removedids:
			continue
		# Get everything that is attached to the parent bus
		loadsiblings = loadbus_obj.get('!CNXNS','None')
		loadsiblings = loadsiblings.replace('[','').replace(']','')
		loadsiblings = loadsiblings.split(',')
		# Does the loadbus connect to a transformer? If not, move to next object in treecopy
		xfrmrids = [x for x in loadsiblings if x.startswith('transformer.')] # only checks for immediately adjacent transformer. Use mergecontiglines first to condense similar line segments
		# Are other devices connected to the loadbus? If so, move to next object in treecopy
		loadids = [x for x in loadsiblings if x.startswith('load.')]
		if len(loadsiblings)-len(xfrmrids) != len(loadids):
			continue
		xfrmrids = list(set(xfrmrids)) # 3-winding xfrmrs often define two connections to the same bus (i.e. split-phase connections)
		if len(xfrmrids) != 1:
			continue
		#everything checks out. Begin modifications.
		# Get xfrmr parent/primary winding bus id
		xfrmrid = xfrmrids[0]
		xfrmr_obj = tree[name2key[xfrmrid]]
		xfrmrcnxns = xfrmr_obj.get('buses','None')
		xfrmrcnxns = xfrmrcnxns.replace('[','').replace(']','')
		xfrmrcnxns = xfrmrcnxns.split(',')
		xfrmrbusid = xfrmrcnxns[0].split('.',1)[0] # by convention, the primary winding is first
		# Get xfrmr primary winding connection code
		xfrmrconncode = xfrmrcnxns[0].split('.',1)[1]
		# Get xfrmr primary winding connection type (i.e. delta/wye)
		xfrmrconntype = xfrmr_obj.get('conns').replace(']','').replace('[','')
		xfrmrconntype = xfrmrconntype.split(',')[0] # by convention, the primary winding is first
		# Get xfrmr primary winding voltage
		#TODO: do we need to check that the base voltages are the same for the secondary windings before setting the load's kv?
		xfrmrkv = xfrmr_obj.get('kvs','None')
		xfrmrkv = xfrmrkv.replace('[','').replace(']','')
		xfrmrkv = xfrmrkv.split(',')
		xfrmrkv = xfrmrkv[0]
		xfrmrphases = [c for c in xfrmrconncode.split('.') if c!='0']
		xfrmrbus_obj = tree[name2key[xfrmrbusid]]
		xfrmrbuscons = xfrmrbus_obj.get('!CNXNS','None')
		xfrmrbuscons = xfrmrbuscons.replace('[','').replace(']','')
		xfrmrbuscons = xfrmrbuscons.split(',')

		load_obj = tree[name2key[objid]]	
		# Connect the load to the xfrmrbus
		load_obj['bus1'] = xfrmrbusid + '.' + xfrmrconncode
		# Set load kv to kv of primary winding.
		load_obj['kv'] = xfrmrkv
		if combine_loads==True:
			# Fix kw values to capture xfrmr losses (2.5%); aggregate kw, kvar, pf with any other sibling loads and correct the number of phases and the parent bus connection.
			newkw = 0
			newkvar = 0
			pfs = []
			for lid in loadids:
				lid_obj = tree[name2key[lid]]
				newkw = newkw + float(lid_obj.get('kw','0'))*1.025
				newkvar = newkvar + float(lid_obj.get('kvar','0'))
				if lid_obj.get('pf','None') != 'None':
					pfs.append(lid_obj.get('pf'))
			load_obj['kw'] = str(newkw)
			if load_obj.get('kvar','None') != 'None':
				load_obj['kvar'] = str(newkvar)
			if len(pfs) >0:
				totpf = 0
				for pf in pfs:
					totpf += float(pf)
				load_obj['pf'] = str(totpf/len(pfs))
			# Correct the number of phases on the load
			if xfrmrconntype == 'delta':
				load_obj['phases'] = str(len(xfrmrphases)-1)
			else:
				load_obj['phases'] = str(len(xfrmrphases))
			# Add load and remove transformer from xfrmrbus connections
			if xfrmrid in xfrmrbuscons:
				xfrmrbuscons.remove(xfrmrid)
			cstr = '['
			for elm in xfrmrbuscons:
				cstr += elm + ','
			cstr += objid + ','
			cstr = cstr[:-1] + ']'
			xfrmrbus_obj['!CNXNS'] = cstr
			# Update the new load and its new parent bus in tree
			tree[name2key[xfrmrbusid]] = xfrmrbus_obj
			tree[name2key[objid]] = load_obj
			# Remove from tree: Aggregated loads, xfrmr, loadbus
			for ld in loadids:
				if ld != objid:
					removedids.append(ld)
					del tree[name2key[ld]]
			removedids.append(xfrmrid)
			del tree[name2key[xfrmrid]]
			removedids.append(loadbusid)
			del tree[name2key[loadbusid]]
		else:
			for lid in loadids:
				lid_obj = tree[name2key[lid]]
				# Fix load kw values to capture xfrmr losses (2.5%)
				tree[name2key[lid["kw"]]] = float(lid_obj.get('kw','0'))*1.025
				# Correct the number of phases on the loads
				if xfrmrconntype == 'delta':
					lid_obj['phases'] = str(len(xfrmrphases)-1)
				else:
					lid_obj['phases'] = str(len(xfrmrphases))
				# update this load in tree
				tree[name2key[lid]] = lid_obj
			# Add load and remove transformer from xfrmrbus connections
			if xfrmrid in xfrmrbuscons:
				xfrmrbuscons.remove(xfrmrid)
			cstr = '['
			for elm in xfrmrbuscons:
				cstr += elm + ','
			for ld in loadids:
				cstr += ld + ','
			cstr = cstr[:-1] + ']'
			xfrmrbus_obj['!CNXNS'] = cstr
			# Update thenew parent bus in tree
			tree[name2key[xfrmrbusid]] = xfrmrbus_obj
			# Remove from tree: xfrmr, loadbus
			removedids.append(xfrmrid)
			del tree[name2key[xfrmrid]]
			removedids.append(loadbusid)
			del tree[name2key[loadbusid]]
	tree = [v for k,v in tree.items()] # back to a list of dicts
	tree = removeCnxns(tree)
	if os.path.exists('removed_ids.txt'):
		os.remove('removed_ids.txt')
	with open('removed_ids.txt', 'a') as remfile:
		for remid in removedids:
			remfile.write(remid + '\n')
	return tree

def _tests():
	from omf.solvers.opendss.dssConvert import dssToTree, distNetViz, evilDssTreeToGldTree, treeToDss, evilGldTreeToDssTree
	fpath = ['ieee37.clean.dss','ieee123_solarRamp.clean.dss','iowa240.clean.dss','ieeeLVTestCase.clean.dss','ieee8500-unbal_no_fuses.clean.dss']

	for fname in fpath:
		outdir = omf.omfDir + '/solvers/opendss/voltageCompare_' + fname[:-4]
		ckt = omf.omfDir + '/solvers/opendss/' + fname
		print('!!!!!!!!!!!!!! ',ckt,' !!!!!!!!!!!!!!')
		# Test for reduceCircuit, voltageCompare, getVoltages, and runDSS.
		tree = dssToTree(ckt)
		#voltagePlot(ckt,PU=False)
		#gldtree = evilDssTreeToGldTree(tree) # DEBUG
		#distNetViz.viz_mem(gldtree, open_file=True, forceLayout=True) # DEBUG
		oldsz = len(tree)
		tree = reduceCircuit(tree)
		newsz = len(tree)
		#gldtree = evilDssTreeToGldTree(tree) # DEBUG
		#distNetViz.viz_mem(gldtree, open_file=True, forceLayout=True) # DEBUG
		#tree = evilGldTreeToDssTree(gldtree) # DEBUG
		# outckt_loc = ckt[:-4] + '_reduced.dss'
		treeToDss(tree, ckt+'out.dss')
		#voltagePlot(outckt_loc,PU=False)
		# if not os.path.exists(outdir):
		# 	os.mkdir(outdir)
		# involts_loc = ckt[:-4] + '_volts.dss'
		# involts = getVoltages(ckt, keep_output=True, outdir=outdir, output_filename=involts_loc)
		# outvolts_loc = outckt_loc[:-4] + '_volts.dss'
		# outvolts = getVoltages(outckt_loc, keep_output=True, outdir=outdir, output_filename=outvolts_loc)
		# rsumm_P, rsumm_D = voltageCompare(involts, outvolts, saveascsv=True, with_plots=False, outdir=outdir, outfilebase=ckt[:-4])		
		# maxPerrM = [rsumm_P.loc['RMSPE',c] for c in rsumm_P.columns if c.lower().startswith(' magnitude')]
		# maxPerrM = pd.Series(maxPerrM).max()
		# maxPerrA = [rsumm_P.loc['RMSPE',c] for c in rsumm_P.columns if c.lower().startswith(' angle')]
		# maxPerrA = pd.Series(maxPerrA).max()
		# maxDerrA = [rsumm_D.loc['RMSE',c] for c in rsumm_D.columns if c.lower().startswith(' angle')]
		# maxDerrA = pd.Series(maxDerrA).max()
		# maxDerrM = [rsumm_D.loc['RMSE',c] for c in rsumm_D.columns if c.lower().startswith(' magnitude')]
		# maxDerrM = pd.Series(maxDerrM).max()
		# from shutil import rmtree
		# os.remove(outckt_loc)
		# rmtree(outdir)
		#print('Objects removed: %s (of %s).\nPercent reduction: %s%%\nMax RMSPE for voltage magnitude: %s%%\nMax RMSPE for voltage angle: %s%%\nMax RMSE for voltage magnitude: %s\nMax RMSE for voltage angle: %s\n'%(oldsz-newsz, oldsz, (oldsz-newsz)*100/oldsz, maxPerrM, maxPerrA, maxDerrM, maxDerrA)) # DEBUG
		# errlim = 0.30 # threshold of 30% error between reduced files. 
		# assert maxPerrM <= errlim*100, 'The voltage magnitude error between the compared files exceeds the allowable limit of %s%%.'%(errlim*100)
		
def _runTest():
	# runDSS('nreca1824.dss', keep_output=False)
	runDSS(omf.omfDir + '/iowa240.clean.dss', keep_output=False)

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
	# _runTest()
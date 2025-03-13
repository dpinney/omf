''' Calculate hosting capacity using model_based and/or AMI-based methods. '''
import shutil
import plotly as py
import plotly.express as px
import pandas as pd
import numpy as np
from pathlib import Path
import time
import networkx as nx

# OMF imports
import omf
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
from omf.solvers import opendss
from omf.solvers import mohca_cl

# Model metadata:
tooltip = "Calculate hosting capacity using model_based and/or AMI-based methods."
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = False

def convert_seconds_to_hms_ms( seconds ):
	milliseconds = seconds * 1000
	# Calculate hours, minutes, seconds, and milliseconds
	hours, remainder = divmod(milliseconds, 3600000)
	minutes, remainder = divmod(remainder, 60000)
	seconds, milliseconds = divmod(remainder, 1000)
	return "{:02d}:{:02d}:{:02d}.{:03d}".format(int(hours), int(minutes), int(seconds), int(milliseconds))

def sandia_algo_post_check(modelDir):
	retVal = False
	mohcaLog = [x for x in os.listdir(modelDir) if x.endswith('.log')][0]
	try:
		with open( Path(modelDir, mohcaLog), 'r', encoding="utf-8") as file:
			for line in file:
				splitLine = line.split(" - ")
				if len(splitLine) > 3:
					splitWords = splitLine[3].split(" ")
					if splitWords[4].lower() == "q":
						retVal = True
	except FileNotFoundError as e:
		print("HostingCapacity - ModelFree Sandia Algorithm - mohca_sandia.log file not found: ", {e})
	return retVal

def hosting_capacity_map( modelDir, inputDict, outData ):
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0]
	path_to_omd = Path(modelDir, feederName)
	starting_omd = json.load(open(path_to_omd)) 

	# Starting there are no warnings
	outData['mapWarningFlag'] = False
	outData['hideMap'] = False

	if inputDict['runAmiAlgorithm'] == 'on':
		model_free_data = Path(modelDir, 'output_model_free_full.csv')
		model_free_data_df = pd.read_csv(model_free_data)
		with open(path_to_omd) as f:
			omd = json.load(f)
		buses_from_omd_tree = []
		for k, v in omd['tree'].items():
			if v['object'] == 'bus':
				buses_from_omd_tree.append(v['name'])
		model_free_buses = model_free_data_df['busname'].unique()
		# Finding the buses from mohca thats in the circuit. this is what we will color
		model_free_buses_in_omd_file = list(set(model_free_buses).intersection(buses_from_omd_tree))
		if len(model_free_buses_in_omd_file) != 0:
			# Great, there are some buses in the mohca file that are in the omd file. That means we can have some color!
			# Note: If buses are in the omd and not in the Model-Free results, nothing is done.
			# 			If buses are in the Model-Free results and not in the omd, nothing is done.
			# If this were to change:
			# - These are the buses that are in the model-free results and not in the omd file they would have to get dropped.
			# 	buses_in_mohca_not_in_omd = set(mohca_buses) - set(buses_from_omd_tree)
			attachment_keys = {
				"coloringFiles": {
					"output_model_free_full.csv": {
						"csv": "<content>",
						"colorOnLoadColumnIndex": "1"
					}
				}
			}
			model_free_color_data = Path(modelDir, 'output_model_free_full.csv').read_text()
			# adding the mohca color output to the attachment
			attachment_keys['coloringFiles']['output_model_free_full.csv']['csv'] = model_free_color_data
			new_omd_path = Path(modelDir, 'color.omd')
			starting_omd['attachments'] = attachment_keys
			with open(new_omd_path, 'w+') as out_file:
				json.dump(starting_omd, out_file, indent=4)
			omf.geo.map_omd(new_omd_path, modelDir, open_browser=False)
			outData['hostingCapacityMap'] = open(Path(modelDir, "geoJson_offline.html"), 'r').read()
		else:
			# Warning there are no buses 
			outData['mapWarningFlag'] = True
			outData['mapWarningInfo'] = f"There are no buses in the .csv file that was provided for the model-free algorithm that are present in the circuit file. Map display may be affected."

	if inputDict['runModelBasedAlgorithm'] == 'on':
		# This code is copied from what previously existed in run_model_based_algorithm
		# Except now, we are gonna check if color.omd is created.
		# If it is, then we just need to add the results to the already existing stuff
		# If its not, that means we need to create the map fresh.
		colorPath = Path(modelDir, 'color.omd')
		if colorPath.exists():
			# Just add model-based coloring
				model_based_color = {
					"color_by_model_based.csv": {
						"csv": "<content>",
						"colorOnLoadColumnIndex": "0"
					}
				}
				model_based_color_data = Path(modelDir, 'color_by_model_based.csv').read_text()
				original_file_data = json.load( open(colorPath) )
				original_file_data['attachments']['coloringFiles'].update(model_based_color)
				original_file_data['attachments']['coloringFiles']['color_by_model_based.csv']['csv'] = model_based_color_data
				with open(colorPath, 'w+') as out_file:
					json.dump(original_file_data, out_file, indent=4)
				omf.geo.map_omd(colorPath, modelDir, open_browser=False )
				outData['hostingCapacityMap'] = open(Path(modelDir, "geoJson_offline.html"), 'r' ).read()
		else:
			attachment_keys = {
				"coloringFiles": {
				"color_by_model_based.csv": {
					"csv": "<content>",
					"colorOnLoadColumnIndex": "1"
				},
				}
			}
			
			model_based_color_data = Path(modelDir, 'color_by_model_based.csv').read_text()
			attachment_keys['coloringFiles']['color_by_model_based.csv']['csv'] = model_based_color_data
			new_omd_path = Path(modelDir, 'color.omd')
			starting_omd['attachments'] = attachment_keys
			with open(new_omd_path, 'w+') as out_file:
				json.dump(starting_omd, out_file, indent=4)
			omf.geo.map_omd(new_omd_path, modelDir, open_browser=False )
			outData['hostingCapacityMap'] = open(Path(modelDir, "geoJson_offline.html"), 'r' ).read()
	if inputDict['runDownlineAlgorithm'] == 'on':
		# Same thing as the above if. We need to check if its created already. If it is, we just adding the color, if its not, we need to create the map setup as well
		colorPath = Path(modelDir, 'color.omd')
		if colorPath.exists():
			downline_color_data = Path(modelDir, 'output_downline_load.csv').read_text()
			downline_color = {
				"output_downline_load.csv": {
					"csv": "<content>",
					"colorOnLoadColumnIndex": "0"
				}
			}
			original_file_data = json.load( open(colorPath) )
			original_file_data['attachments']['coloringFiles'].update(downline_color)
			original_file_data['attachments']['coloringFiles']['output_downline_load.csv']['csv'] = downline_color_data
			with open(colorPath, 'w+') as out_file:
				json.dump(original_file_data, out_file, indent=4)
			omf.geo.map_omd(colorPath, modelDir, open_browser=False )
			outData['hostingCapacityMap'] = open(Path(modelDir, "geoJson_offline.html"), 'r' ).read()
		else:
			attachment_keys = {
				"coloringFiles": {
				"output_downline_load.csv": {
					"csv": "<content>",
					"colorOnLoadColumnIndex": "1"
				},
				}
			}
			downline_load_color_data = Path(modelDir, 'output_downline_load.csv').read_text()
			attachment_keys['coloringFiles']['output_downline_load.csv']['csv'] = downline_load_color_data
			new_omd_path = Path(modelDir, 'color.omd')
			starting_omd['attachments'] = attachment_keys
			with open(new_omd_path, 'w+') as out_file:
				json.dump(starting_omd, out_file, indent=4)
			omf.geo.map_omd(new_omd_path, modelDir, open_browser=False )
			outData['hostingCapacityMap'] = open(Path(modelDir, "geoJson_offline.html"), 'r' ).read()

	if outData["mapWarningFlag"] == True and inputDict['runModelBasedAlgorithm'] == 'off' and inputDict['runDownlineAlgorithm'] == 'off':
		# If there are no buses in the .csv that match the circuit, and model based and downline load both are not running, we don't need the map
		outData["hideMap"] = True

def run_downline_load_algorithm( modelDir, inputDict, outData ):
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0]
	path_to_omd = Path(modelDir, feederName)
	tree = opendss.dssConvert.omdToTree(path_to_omd)
	opendss.dssConvert.treeToDss(tree, Path(modelDir, 'downlineLoad.dss'))
	downline_start_time = time.time()
	nx_data = opendss.dss_to_nx_fulldata( os.path.join( modelDir, 'downlineLoad.dss') )
	graph = nx_data[0]
	buses = opendss.get_all_buses( os.path.join( modelDir, 'downlineLoad.dss') )
	buses_output = {}
	objectTypesFromGraph = nx.get_node_attributes(graph, 'object')

	kwFromGraph = nx.get_node_attributes(graph, 'kw') #Load, generator attribute
	kwRatedFromGraph = nx.get_node_attributes( graph, 'kwrated') # Storage attribute
	kvFromGraph = nx.get_node_attributes( graph, 'kv' )
	# Check if they are buses
	for bus in buses:
		if bus in graph.nodes:
			kwSum = 0
			get_dependents = sorted(nx.descendants(graph, bus))
			for dependent in get_dependents:
				if dependent in kwFromGraph.keys() and objectTypesFromGraph[dependent] == 'load':
					kwSum += float( kwFromGraph[dependent] )
				elif dependent in kwFromGraph.keys() and objectTypesFromGraph[dependent] == 'generator':
					kwSum -= float( kwFromGraph[dependent] )
				elif dependent in kwRatedFromGraph.keys() and objectTypesFromGraph[dependent] == 'storage':
					kwSum -= float( kwRatedFromGraph[dependent] )
				elif dependent in kvFromGraph.keys() and objectTypesFromGraph[dependent] == 'pvsystem':
					pfFromGraph = nx.get_node_attributes(graph, 'pf')
					# pvsystem has kv, not kw
					kwForPVSys = kvFromGraph[dependent] * pfFromGraph[dependent]
					kwSum -= kwForPVSys
			buses_output[bus] = kwSum
	downline_output = pd.DataFrame(list(buses_output.items()), columns=['bus', 'kw'] )
	downline_end_time = time.time()
	sorted_downlineDF = downline_output.sort_values(by='bus')
	buses_to_remove = ['eq_source_bus', 'bus_xfmr']
	indexes = []
	for bus in buses_to_remove:
		indexes.append( sorted_downlineDF[sorted_downlineDF['bus'] == bus].index )
	for i in indexes:
		sorted_downlineDF = sorted_downlineDF.drop(i)
	sorted_downlineDF.to_csv(Path(modelDir, 'output_downline_load.csv'), index=False)

	outData['downline_tableHeadings'] = downline_output.columns.values.tolist()
	outData['downline_tableValues'] = (list(sorted_downlineDF.itertuples(index=False, name=None)))
	outData['downline_runtime'] = convert_seconds_to_hms_ms( downline_end_time - downline_start_time )
	return sorted_downlineDF

def check_kvar_sandia_func( inputPath ):
	data = pd.read_csv(inputPath)
	if 'kvar_reading' in data:
		# Returns False if no q
		return mohca_cl.sandia.get_has_input_q(data)
	else:
		return False
	

def run_ami_algorithm( modelDir, inputDict, outData ):
	# mohca data-driven hosting capacity
	inputPath = Path(modelDir, inputDict['AMIDataFileName'])
	inputAsString = inputPath.read_text()
	output_path_vchc = Path(modelDir, 'output_mohca_vchc.csv')
	output_path_tchc = Path(modelDir, 'output_mohca_tchc.csv')

	completed_xfmr_cust_pairing_path = Path(modelDir, inputDict['xfmr_cust_completed_data_filename'])
	completed_xfmr_cust_df = pd.read_csv(completed_xfmr_cust_pairing_path)
	calculate_xfmr_cust_pairing_path = Path(modelDir, inputDict['xfmr_cust_calculate_data_filename'])

	bus_coords_input = Path(modelDir, inputDict['bus_coords_data_filename'])

	isu_calc_result_filename = "isu_calc_result.csv"
	isu_calc_result_filepath = Path(modelDir, isu_calc_result_filename )

	try:
		csvValidateAndLoad(inputAsString, modelDir=modelDir, header=0, nrows=None, ncols=None, dtypes=[], return_type='df', ignore_nans=True, save_file=None, ignore_errors=False )
	except:
		errorMessage = "AMI-Data CSV file is incorrect format. Please see valid format definition at <a target='_blank' href='https://github.com/dpinney/omf/wiki/Models-~-hostingCapacity#meter-data-input-csv-file-format'>OMF Wiki hostingCapacity</a>"
		raise Exception(errorMessage)

	vv_points_eval = [float(x) for x in inputDict['vv_points'].split(',')]
	vv_x = [v for i,v in enumerate(vv_points_eval) if i%2==0]
	vv_y = [v for i,v in enumerate(vv_points_eval) if i%2==1]

	xf_lookup_input_df = pd.read_csv( Path(modelDir, inputDict['xf_lookup_data_filename']) )
	if xf_lookup_input_df.empty:
		xf_lookup_arg = None
	else:
		xf_lookup_arg = xf_lookup_input_df

	hasKvar = check_kvar_sandia_func( inputPath )
	
	AMI_start_time = time.time()
	if inputDict[ "algorithm" ] == "sandia1":
		exactFlag = False
		if inputDict["dgInverterSetting"] == 'constantPF':
			# Calculate Voltage Hosting Capacity
			mohca_cl.sandia1( in_path=inputPath, out_path=output_path_vchc, der_pf= float(inputDict['der_pf']), vv_x=None, vv_y=None, load_pf_est=float(inputDict['load_pf_est'] ))
			if hasKvar:
				# Calculate Thermal Hosting Capacity
				# Check if user inputted their own completed xfmr <-> customer mappings. If so, calculate with theirs
				if completed_xfmr_cust_df.empty == False:
					mohca_cl.sandiaTCHC( in_path=inputPath, out_path=output_path_tchc, final_results=completed_xfmr_cust_df, der_pf=float(inputDict['der_pf']), vv_x=None, vv_y=None, overload_constraint=float(inputDict['overload_constraint']), xf_lookup=xf_lookup_arg )
				# If they did not include their own, calculate it as best as you can with ISU's function, then calculate thermal with the result of ISU's
				else:
					if inputDict['num_of_xfmrs'] == 0:
						num_of_xfmr = None
					else:
						num_of_xfmr = int( inputDict['num_of_xfmrs'])
						exactFlag = True
					isu_xfmr_cust_map_result_df = mohca_cl.isu_transformerCustMapping(input_meter_data_fp=inputPath, grouping_output_fp=isu_calc_result_filepath, minimum_xfmr_n=num_of_xfmr, fmr_n_is_exact=exactFlag, bus_coords_fp=bus_coords_input )
					mohca_cl.sandiaTCHC( in_path=inputPath, out_path=output_path_tchc, final_results=isu_xfmr_cust_map_result_df, der_pf=float(inputDict['der_pf']), vv_x=None, vv_y=None, overload_constraint=float(inputDict['overload_constraint']), xf_lookup=xf_lookup_arg )
			else:
				outData["reactivePowerWarningFlag"] = True
				outData["reactivePowerWarningInfo"] = f"Reactive Power not present in Meter Data Input File. Results will only show ESTIMATED voltage model-free results. Thermal model-free results are NOT avaiable"
		elif inputDict["dgInverterSetting"] == 'voltVar':
			# Calculate Voltage Hosting Capacity
			mohca_cl.sandia1( in_path=inputPath, out_path=output_path_vchc, der_pf= float(inputDict['der_pf']), vv_x=vv_x, vv_y=vv_y, load_pf_est=float(inputDict['load_pf_est'] ))
			if hasKvar:
				# Calculate Thermal Hosting Capacity
				if completed_xfmr_cust_df.empty == False:
					mohca_cl.sandiaTCHC( in_path=inputPath, out_path=output_path_tchc, final_results=completed_xfmr_cust_df, der_pf=float(inputDict['der_pf']), vv_x=vv_x, vv_y=vv_y, overload_constraint=float(inputDict['overload_constraint']), xf_lookup=xf_lookup_arg )
				else:
					if inputDict['num_of_xfmrs'] == 0:
						num_of_xfmr = None
					else:
						num_of_xfmr = int( inputDict['num_of_xfmrs'])
						exactFlag = True
					isu_xfmr_cust_map_result_df = mohca_cl.isu_transformerCustMapping(input_meter_data_fp=inputPath, grouping_output_fp=isu_calc_result_filepath, minimum_xfmr_n=num_of_xfmr, fmr_n_is_exact=exactFlag, bus_coords_fp=bus_coords_input )
					mohca_cl.sandiaTCHC( in_path=inputPath, out_path=output_path_tchc, final_results=isu_xfmr_cust_map_result_df, der_pf=float(inputDict['der_pf']), vv_x=vv_x, vv_y=vv_y, overload_constraint=float(inputDict['overload_constraint']), xf_lookup=xf_lookup_arg )
			else:
				outData["reactivePowerWarningFlag"] = True
				outData["reactivePowerWarningInfo"] = f"Reactive power not present in Meter Data Input File. Model-Free Voltage results will be estimated. No model-free thermal results available."
		else:
			errorMessage = "DG Error - Should not happen. dgInverterSetting is not either of the 2 options it is supposed to be."
			raise Exception(errorMessage)
	elif inputDict[ "algorithm" ] == "iastate":
		mohca_cl.iastate( inputPath, output_path_vchc )
	else:
		errorMessage = "Algorithm name error"
		raise Exception(errorMessage)
	AMI_end_time = time.time()
	model_free_results = pd.read_csv( output_path_vchc, index_col=False)
	model_free_results.rename(columns={'kw_hostable': 'voltage_cap_kW'}, inplace=True)
	model_free_results_sorted = model_free_results.sort_values(by='busname')
	if hasKvar:
		model_free_thermal_results = pd.read_csv( output_path_tchc )
		thermal_kw_results = model_free_thermal_results['TCHC (kW)']
		model_free_results_sorted['thermal_cap_kW'] = thermal_kw_results
		histogramFigure = px.histogram( model_free_results_sorted, x=['voltage_cap_kW', 'thermal_cap_kW'], template="simple_white", color_discrete_sequence=["lightblue", "MediumPurple"] )
		histogramFigure.update_layout(bargap=0.5)
		model_free_results_sorted['min_allowed_kW'] = np.minimum( model_free_results_sorted['voltage_cap_kW'], model_free_results_sorted['thermal_cap_kW'])
		model_free_results_sorted = model_free_results_sorted[['busname', 'min_allowed_kW', 'voltage_cap_kW', 'thermal_cap_kW']]
		barChartFigure = px.bar(model_free_results_sorted, x='busname', y=['min_allowed_kW','voltage_cap_kW', 'thermal_cap_kW'], barmode='group', color_discrete_sequence=["green", "lightblue", "MediumPurple"], template="simple_white" )
		barChartFigure.update_layout( legend=dict(
			orientation='h',
			yanchor='bottom',
			y=1.02,
			xanchor='right',
			x=1
		) )
	else:
		histogramFigure = px.histogram( model_free_results_sorted, x=['voltage_cap_kW'], template="simple_white", color_discrete_sequence=["lightblue"] )
		histogramFigure.update_layout(bargap=0.5)
		model_free_results_sorted['min_allowed_kW'] = model_free_results_sorted['voltage_cap_kW']
		model_free_results_sorted = model_free_results_sorted[['busname', 'min_allowed_kW', 'voltage_cap_kW']]
		barChartFigure = px.bar(model_free_results_sorted, x='busname', y=['min_allowed_kW','voltage_cap_kW'], barmode='group', color_discrete_sequence=["green", "lightblue"], template="simple_white" )
		barChartFigure.update_layout( legend=dict(
			orientation='h',
			yanchor='bottom',
			y=1.02,
			xanchor='right',
			x=1
		) )
	model_free_results_sorted.to_csv( Path(modelDir, "output_model_free_full.csv"), index=False )
	barChartFigure.add_traces( list(px.line(model_free_results_sorted, x='busname', y='min_allowed_kW', markers=True).select_traces()) )
	outData['histogramFigure'] = json.dumps( histogramFigure, cls=py.utils.PlotlyJSONEncoder )
	outData['barChartFigure'] = json.dumps( barChartFigure, cls=py.utils.PlotlyJSONEncoder )
	outData['AMI_tableHeadings'] = model_free_results_sorted.columns.values.tolist()
	outData['AMI_tableValues'] = ( list(model_free_results_sorted.itertuples(index=False, name=None)) )
	outData['AMI_runtime'] = convert_seconds_to_hms_ms( AMI_end_time - AMI_start_time )

def run_model_based_algorithm( modelDir, inputDict, outData ):
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0]
	inputDict['feederName1'] = feederName[:-4]
	path_to_omd = Path(modelDir, feederName)
	tree = opendss.dssConvert.omdToTree(path_to_omd)
	opendss.dssConvert.treeToDss(tree, Path(modelDir, 'circuit.dss'))
	model_based_start_time = time.time()
	model_basedHCResults = opendss.hosting_capacity_all( FNAME = Path(modelDir, 'circuit.dss'), max_test_kw=int(inputDict["model_basedHCMaxTestkw"]))
	model_based_end_time = time.time()
	# - opendss.hosting_capacity_all() changes the cwd, so change it back so other code isn't affected

	model_basedHCDF = pd.DataFrame( model_basedHCResults )
	sorted_model_basedHCDF = model_basedHCDF.sort_values(by='bus')
	sorted_model_basedHCDF.to_csv( "output_tradHC.csv")
	model_basedHCFigure = px.bar( sorted_model_basedHCDF, x='bus', y='max_kw', barmode='group', template='simple_white', color_discrete_sequence=["green"] )
	model_basedHCFigure.update_xaxes(categoryorder='array', categoryarray=sorted_model_basedHCDF.bus.values)
	# These files need to be made for coloring the map.
	color_df = sorted_model_basedHCDF[['bus','max_kw']]
	color_df.to_csv(Path(modelDir, 'color_by_model_based.csv'), index=False)
	outData['model_basedGraphData'] = json.dumps(model_basedHCFigure, cls=py.utils.PlotlyJSONEncoder )
	outData['model_basedHCTableHeadings'] = sorted_model_basedHCDF.columns.values.tolist()
	outData['model_basedHCTableValues'] = (list(sorted_model_basedHCDF.itertuples(index=False, name=None)))
	outData['model_basedRuntime'] = convert_seconds_to_hms_ms( model_based_end_time - model_based_start_time )
	outData['model_basedHCResults'] = model_basedHCResults

def runtimeEstimate(modelDir):
	''' Estimated runtime of model in minutes. '''
	return 1.0

def work(modelDir, inputDict):
	outData = {}
	if inputDict['runAmiAlgorithm'] == 'on':
		run_ami_algorithm(modelDir, inputDict, outData)
	if inputDict.get('runModelBasedAlgorithm', outData) == 'on':
		run_model_based_algorithm(modelDir, inputDict, outData)
	if inputDict.get('runDownlineAlgorithm') == 'on':
		run_downline_load_algorithm( modelDir, inputDict, outData)

	hosting_capacity_map(modelDir=modelDir, inputDict=inputDict, outData=outData)

	outData['stdout'] = "Success"
	outData['stderr'] = ""
	return outData

'''
meter_file_name = input_mohca.csv
The name choice is a standard name. Every file that gets inputted will be changed into that name.
This file comes from a sample input from Sandia to match the secondaryTestCircuit
'''

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	meter_file_name = 'input_mohcaData.csv'
	meter_file_path = Path(omf.omfDir,'static','testFiles', 'hostingCapacity', meter_file_name)
	xfmr_cust_calculate_file_name = 'input_xfmr_cust_calculate.csv'
	xfmr_cust_calculate_file_path = Path( omf.omfDir,'static','testFiles', 'hostingCapacity', xfmr_cust_calculate_file_name )
	xfmr_cust_completed_file_name = 'input_xfmr_cust_completed.csv'
	xfmr_cust_completed_file_path = Path(omf.omfDir, 'static', 'testFiles', 'hostingCapacity', xfmr_cust_completed_file_name)
	xf_lookup_file_name = "input_xf_lookup.csv"
	xf_lookup_file_path = Path( omf.omfDir, 'static','testFiles', 'hostingCapacity', xf_lookup_file_name )
	bus_coords_file_name = "input_bus_coords.csv"
	bus_coords_file_path = Path(omf.omfDir, 'static', 'testFiles', 'hostingCapacity', bus_coords_file_name)

	defaultInputs = {
		"modelType": modelName,
		"algorithm": 'sandia1',
		"AMIDataFileName": meter_file_name,
		"userAMIDisplayFileName": meter_file_name,
		"feederName1": 'nreca_secondaryTestSet',
		"runAmiAlgorithm": 'on',
		"runModelBasedAlgorithm": 'on',
		"runDownlineAlgorithm": 'on',
		"model_basedHCMaxTestkw": 50000,
		"dgInverterSetting": 'constantPF',
		"der_pf": 1.00,
		"vv_points": "0.8,0.44,0.92,0.44,0.98,0,1.02,0,1.08,-0.44,1.2,-0.44",
		"load_pf_est": 1.0,
		"overload_constraint": 1.2,
		"xf_lookup_data_filename": xf_lookup_file_name,
		"xf_lookup_display_filename": xf_lookup_file_name,
		"xfmr_cust_calculate_data_filename": xfmr_cust_calculate_file_name,
		"xfmr_cust_calculate_display_filename": xfmr_cust_calculate_file_name,
		"xfmr_cust_completed_data_filename": xfmr_cust_completed_file_name,
		"xfmr_cust_completed_display_filename": xfmr_cust_completed_file_name,
		"bus_coords_display_filename": bus_coords_file_name,
		"bus_coords_data_filename": bus_coords_file_name,
		"num_of_xfmrs": 12

	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	# Copy files from the test directory ( or respective places ) and put them in the model for use
	try:
		shutil.copyfile(
			Path(__neoMetaModel__._omfDir, "static", "testFiles", 'hostingCapacity', defaultInputs["feederName1"]+'.omd'),
			Path(modelDir, defaultInputs["feederName1"]+'.omd'))
		shutil.copyfile( meter_file_path, Path(modelDir, meter_file_name) )
		shutil.copyfile( xf_lookup_file_path, Path(modelDir, xf_lookup_file_name) )
		shutil.copyfile( xfmr_cust_calculate_file_path, Path(modelDir, xfmr_cust_calculate_file_name) )
		shutil.copyfile( xfmr_cust_completed_file_path, Path(modelDir, xfmr_cust_completed_file_name) )
		shutil.copyfile( bus_coords_file_path, Path(modelDir, bus_coords_file_name))
	except:
		return False
	return creationCode

@neoMetaModel_test_setup
def _disabled_tests():
	# Location
	modelLoc = Path(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		pass # No previous test results.
	# Create New.
	new(modelLoc)
	# Pre-run.
	__neoMetaModel__.renderAndShow(modelLoc)
	# Run the model.
	__neoMetaModel__.runForeground(modelLoc)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
	_disabled_tests()

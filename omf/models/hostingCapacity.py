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
		model_free_data = Path(modelDir, 'output_mohca.csv')
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
					"output_mohca.csv": {
						"csv": "<content>",
						"colorOnLoadColumnIndex": "1"
					}
				}
			}
			model_free_color_data = Path(modelDir, 'output_mohca.csv').read_text()
			# adding the mohca color output to the attachment
			attachment_keys['coloringFiles']['output_mohca.csv']['csv'] = model_free_color_data
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

def run_ami_algorithm( modelDir, inputDict, outData ):
	# mohca data-driven hosting capacity
	inputPath = Path(modelDir, inputDict['AMIDataFileName'])
	inputAsString = inputPath.read_text()
	outputPath = Path(modelDir, 'output_mohca.csv')
	try:
		csvValidateAndLoad(inputAsString, modelDir=modelDir, header=0, nrows=None, ncols=None, dtypes=[], return_type='df', ignore_nans=True, save_file=None, ignore_errors=False )
	except:
		errorMessage = "AMI-Data CSV file is incorrect format. Please see valid format definition at <a target='_blank' href='https://github.com/dpinney/omf/wiki/Models-~-hostingCapacity#meter-data-input-csv-file-format'>OMF Wiki hostingCapacity</a>"
		raise Exception(errorMessage)

	vv_points_eval = [float(x) for x in inputDict['vv_points'].split(',')]
	vv_x = [v for i,v in enumerate(vv_points_eval) if i%2==0]
	vv_y = [v for i,v in enumerate(vv_points_eval) if i%2==1]

	AMI_start_time = time.time()
	if inputDict[ "algorithm" ] == "sandia1":
		if inputDict["dgInverterSetting"] == 'constantPF':
			mohca_cl.sandia1( in_path=inputPath, out_path=outputPath, der_pf= float(inputDict['der_pf']), vv_x=None, vv_y=None, load_pf_est=float(inputDict['load_pf_est'] ))
		elif inputDict["dgInverterSetting"] == 'voltVar':
			mohca_cl.sandia1( in_path=inputPath, out_path=outputPath, der_pf= float(inputDict['der_pf']), vv_x=vv_x, vv_y=vv_y, load_pf_est=float(inputDict['load_pf_est'] ))
		else:
			errorMessage = "DG Error - Should not happen. dgInverterSetting is not either of the 2 options it is supposed to be."
			raise Exception(errorMessage)
		present_q_warning = sandia_algo_post_check(modelDir=modelDir)
		if present_q_warning == True:
			outData["reactivePowerWarningFlag"] = present_q_warning
			outData["reactivePowerWarningInfo"] = f"Reactive power missing from data set. Estimating hosting capacity through power factor from given input 'Load Power Factor'"
	elif inputDict[ "algorithm" ] == "iastate":
		mohca_cl.iastate( inputPath, outputPath )
	else:
		errorMessage = "Algorithm name error"
		raise Exception(errorMessage)
	AMI_end_time = time.time()
	AMI_results = pd.read_csv( outputPath, index_col=False)
	AMI_results.rename(columns={'kw_hostable': 'voltage_cap_kW'}, inplace=True)
	histogramFigure = px.histogram( AMI_results, x='voltage_cap_kW', template="simple_white", color_discrete_sequence=["MediumPurple"] )
	histogramFigure.update_layout(bargap=0.5)
	# TBD - Needs to be modified when the MoHCA algorithm supports calculating thermal hosting capacity
	min_value = 5
	max_value = 8
	AMI_results['thermal_cap_kW']  = np.random.randint(min_value, max_value + 1, size=len(AMI_results))
	AMI_results['max_cap_allowed_kW'] = np.minimum( AMI_results['voltage_cap_kW'], AMI_results['thermal_cap_kW'])
	AMI_results_sorted = AMI_results.sort_values(by='busname')
	barChartFigure = px.bar(AMI_results_sorted, x='busname', y=['voltage_cap_kW', 'thermal_cap_kW', 'max_cap_allowed_kW'], barmode='group', color_discrete_sequence=["green", "lightblue", "MediumPurple"], template="simple_white" )
	barChartFigure.update_layout( legend=dict(
		orientation='h',
		yanchor='bottom',
		y=1.02,
		xanchor='right',
		x=1
	) )
	barChartFigure.add_traces( list(px.line(AMI_results_sorted, x='busname', y='max_cap_allowed_kW', markers=True).select_traces()) )
	outData['histogramFigure'] = json.dumps( histogramFigure, cls=py.utils.PlotlyJSONEncoder )
	outData['barChartFigure'] = json.dumps( barChartFigure, cls=py.utils.PlotlyJSONEncoder )
	outData['AMI_tableHeadings'] = AMI_results_sorted.columns.values.tolist()
	outData['AMI_tableValues'] = ( list(AMI_results_sorted.itertuples(index=False, name=None)) )
	outData['AMI_runtime'] = convert_seconds_to_hms_ms( AMI_end_time - AMI_start_time )

def run_model_based_algorithm( modelDir, inputDict, outData ):
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0]
	inputDict['feederName1'] = feederName[:-4]
	path_to_omd = Path(modelDir, feederName)
	tree = opendss.dssConvert.omdToTree(path_to_omd)
	opendss.dssConvert.treeToDss(tree, Path(modelDir, 'circuit.dss'))
	model_based_start_time = time.time()
	model_basedHCResults = opendss.hosting_capacity_all( FNAME = Path(modelDir, 'circuit.dss'), max_test_kw=int(inputDict["model_basedHCMaxTestkw"]), multiprocess=False)
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

	# TODO: All are False, then there's no map.
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
	xftable_file_name = 'ST_transformer_customer_mapping_expected.csv'
	xftable_file_path = Path(omf.omfDir,'static','testFiles', 'hostingCapacity', xftable_file_name )
	# meter_file_contents = open(meter_file_path).read()
	defaultInputs = {
		"modelType": modelName,
		"algorithm": 'sandia1',
		"AMIDataFileName": meter_file_name,
		"userAMIDisplayFileName": meter_file_name,
		"feederName1": 'nreca_secondaryTestSet',
		"runModelBasedAlgorithm": 'on',
		"runAmiAlgorithm": 'on',
		"runDownlineAlgorithm": 'on',
		"model_basedHCMaxTestkw": 50000,
		"dgInverterSetting": 'constantPF',
		"der_pf": 1.00,
		"vv_points": "0.8,0.44,0.92,0.44,0.98,0,1.02,0,1.08,-0.44,1.2,-0.44",
		"load_pf_est": 1.0,
		"overload_constraint": 1.2,
		"xf_table_data_time": xftable_file_name,
		"xf_table_display_filename": xftable_file_name

	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	# Copy files from the test directory ( or respective places ) and put them in the model for use
	try:
		shutil.copyfile(
			Path(__neoMetaModel__._omfDir, "static", "testFiles", 'hostingCapacity', defaultInputs["feederName1"]+'.omd'),
			Path(modelDir, defaultInputs["feederName1"]+'.omd'))
		shutil.copyfile( meter_file_path, Path(modelDir, meter_file_name) )
		shutil.copyfile( xftable_file_path, Path(modelDir, xftable_file_name) )
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

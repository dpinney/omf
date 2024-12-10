''' Calculate hosting capacity using traditional and/or AMI-based methods. '''
import shutil
import plotly as py
import plotly.express as px
import plotly.graph_objects as go
# from plotly.subplots import make_subplots
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
tooltip = "Calculate hosting capacity using traditional and/or AMI-based methods."
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = False

def convert_seconds_to_hms_ms( seconds ):
	milliseconds = seconds * 1000
	
	# Calculate hours, minutes, seconds, and milliseconds
	hours, remainder = divmod(milliseconds, 3600000)
	minutes, remainder = divmod(remainder, 60000)
	seconds, milliseconds = divmod(remainder, 1000)
	
	return "{:02d}:{:02d}:{:02d}.{:03d}".format(int(hours), int(minutes), int(seconds), int(milliseconds))

# Deprecated
def bar_chart_coloring( row ):
	color = 'black'
	if row['thermally_limited'] and not row['voltage_limited']:
		color = 'orange'
	elif not row['thermally_limited'] and row['voltage_limited']:
		color = 'yellow'
	elif not row['thermally_limited'] and not row['voltage_limited']:
		color = 'green'
	else:
		color = 'red'
	return color

def run_downline_load_algorithm( modelDir, inputDict, outData ):
	# This uses the circuit - so the tradition needs to be on to do this. 
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
	
	downline_color_data = Path(modelDir, 'output_downline_load.csv').read_text()
	downline_color = {
		"downline_load.csv": {
			"csv": "<content>",
			"colorOnLoadColumnIndex": "0"
		}
	}

	original_file = Path(modelDir, 'color_test.omd') #This should have already been made
	original_file_data = json.load( open(original_file) )

	original_file_data['attachments']['coloringFiles'].update(downline_color)
	original_file_data['attachments']['coloringFiles']['downline_load.csv']['csv'] = downline_color_data

	with open(original_file, 'w+') as out_file:
		json.dump(original_file_data, out_file, indent=4)
	omf.geo.map_omd(original_file, modelDir, open_browser=False )

	outData['traditionalHCMap'] = open(Path(modelDir, "geoJson_offline.html"), 'r' ).read()
	outData['downline_tableHeadings'] = downline_output.columns.values.tolist()
	outData['downline_tableValues'] = (list(sorted_downlineDF.itertuples(index=False, name=None)))
	outData['downline_runtime'] = convert_seconds_to_hms_ms( downline_end_time - downline_start_time )
	return sorted_downlineDF

def run_ami_algorithm( modelDir, inputDict, outData ):
	# mohca data-driven hosting capacity
	inputPath = Path(modelDir, inputDict['AMIDataFileName'])
	inputAsString = inputPath.read_text()

	outputPath = Path(modelDir, 'output_MoCHa.csv')
	AMI_output = []

	try:
		csvValidateAndLoad(inputAsString, modelDir=modelDir, header=0, nrows=None, ncols=None, dtypes=[], return_type='df', ignore_nans=True, save_file=None, ignore_errors=False )
	except:
		errorMessage = "AMI-Data CSV file is incorrect format. Please see valid format definition at <a target='_blank' href='https://github.com/dpinney/omf/wiki/Models-~-hostingCapacity#meter-data-input-csv-file-format'>OMF Wiki hostingCapacity</a>"
		raise Exception(errorMessage)
	
	AMI_start_time = time.time()
	if inputDict[ "algorithm" ] == "sandia1":
		AMI_output = mohca_cl.sandia1( inputPath, outputPath )
	elif inputDict[ "algorithm" ] == "iastate":
		AMI_output = mohca_cl.iastate( inputPath, outputPath )
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
	barChartFigure.add_traces( list(px.line(AMI_results_sorted, x='busname', y='max_cap_allowed_kW', markers=True).select_traces()) )
	outData['histogramFigure'] = json.dumps( histogramFigure, cls=py.utils.PlotlyJSONEncoder )
	outData['barChartFigure'] = json.dumps( barChartFigure, cls=py.utils.PlotlyJSONEncoder )
	outData['AMI_tableHeadings'] = AMI_results_sorted.columns.values.tolist()
	outData['AMI_tableValues'] = ( list(AMI_results_sorted.itertuples(index=False, name=None)) )
	outData['AMI_runtime'] = convert_seconds_to_hms_ms( AMI_end_time - AMI_start_time )

def run_traditional_algorithm( modelDir, inputDict, outData ):
	# traditional hosting capacity if they uploaded an omd circuit file and chose to use it.
	# Check if the file was uploaded and checks to make sure the name matches
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0]
	inputDict['feederName1'] = feederName[:-4]
	path_to_omd = Path(modelDir, feederName)
	tree = opendss.dssConvert.omdToTree(path_to_omd)
	opendss.dssConvert.treeToDss(tree, Path(modelDir, 'circuit.dss'))
	traditional_start_time = time.time()
	traditionalHCResults = opendss.hosting_capacity_all( FNAME = Path(modelDir, 'circuit.dss'), max_test_kw=int(inputDict["traditionalHCMaxTestkw"]), multiprocess=False)
	traditional_end_time = time.time()
	# - opendss.hosting_capacity_all() changes the cwd, so change it back so other code isn't affected
	tradHCDF = pd.DataFrame( traditionalHCResults )
	sorted_tradHCDF = tradHCDF.sort_values(by='bus')
	sorted_tradHCDF.to_csv( "output_tradHC.csv")
	# Don't color bars anymore..
	# sorted_tradHCDF['plot_color'] = sorted_tradHCDF.apply ( lambda row: bar_chart_coloring(row), axis=1 )
	# Plotly has its own colors - need to map the "name" of given colors to theirs
	traditionalHCFigure = px.bar( sorted_tradHCDF, x='bus', y='max_kw', barmode='group', template='simple_white', color_discrete_sequence=["green"] )
	traditionalHCFigure.update_xaxes(categoryorder='array', categoryarray=sorted_tradHCDF.bus.values)
	
	'''
	Other code for bar coloring so there are names when you hover.
	# Map color to violation type to update key/legend
	# colorToKey = {'orange':'thermally_limited', 'yellow': 'voltage_limited', 'red': 'both_violation', 'green': 'no_violation'}
	# Changes the hover mode, key, and legend to show the violation type rather than the color
	traditionalHCFigure.for_each_trace(
		lambda t: t.update(
			name = colorToKey[t.name],
			legendgroup = colorToKey[t.name],
			hovertemplate = t.hovertemplate.replace(t.name, colorToKey[t.name])
			)
		)
	# We don't need the plot_color stuff for anything else, so drop it
	sorted_tradHCDF.drop(sorted_tradHCDF.columns[len(sorted_tradHCDF.columns)-1], axis=1, inplace=True)
	'''
	color_df = sorted_tradHCDF[['bus','max_kw']]
	color_df.to_csv(Path(modelDir, 'color_by_traditional.csv'), index=False)
	attachment_keys = {
		"coloringFiles": {
			"color_by_traditional.csv": {
				"csv": "<content>",
				"colorOnLoadColumnIndex": "1"
			},
		}
	}
	data = Path(modelDir, 'color_by_traditional.csv').read_text()
	attachment_keys['coloringFiles']['color_by_traditional.csv']['csv'] = data
	omd = json.load(open(path_to_omd))
	new_path = Path(modelDir, 'color_test.omd')
	omd['attachments'] = attachment_keys
	with open(new_path, 'w+') as out_file:
		json.dump(omd, out_file, indent=4)
	omf.geo.map_omd(new_path, modelDir, open_browser=False )

	outData['traditionalHCMap'] = open(Path(modelDir, "geoJson_offline.html"), 'r' ).read()
	outData['traditionalGraphData'] = json.dumps(traditionalHCFigure, cls=py.utils.PlotlyJSONEncoder )
	outData['traditionalHCTableHeadings'] = sorted_tradHCDF.columns.values.tolist()
	outData['traditionalHCTableValues'] = (list(sorted_tradHCDF.itertuples(index=False, name=None)))
	outData['traditionalRuntime'] = convert_seconds_to_hms_ms( traditional_end_time - traditional_start_time )
	outData['traditionalHCResults'] = traditionalHCResults

def runtimeEstimate(modelDir):
	''' Estimated runtime of model in minutes. '''
	return 1.0

def work(modelDir, inputDict):
	outData = {}
	
	if inputDict['runAmiAlgorithm'] == 'on':
		run_ami_algorithm(modelDir, inputDict, outData)
	if inputDict.get('optionalCircuitFile', outData) == 'on':
		run_traditional_algorithm(modelDir, inputDict, outData)
	if inputDict.get('runDownlineAlgorithm') == 'on':
		run_downline_load_algorithm( modelDir, inputDict, outData)
	outData['stdout'] = "Success"
	outData['stderr'] = ""
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	meter_file_name = 'input_mohcaCustom.csv'
	meter_file_path = Path(omf.omfDir,'static','testFiles', 'hostingCapacity', meter_file_name)
	# meter_file_contents = open(meter_file_path).read()
	defaultInputs = {
		"modelType": modelName,
		"algorithm": 'sandia1',
		"AMIDataFileName": meter_file_name,
		"userAMIDisplayFileName": meter_file_name,
		"feederName1": 'iowa240.clean.dss',
		"optionalCircuitFile": 'on',
		"traditionalHCMaxTestkw": 50000,
		"dgInverterSetting": 'unityPF',
		"der_pf": 0.95,
		"vv_points": [(0.8,0.44), (0.92, 0.44), (0.98,0), (1.02,0), (1.08,-0.44), (1.2,-0.44)],
		"runAmiAlgorithm": 'on',
		"runDownlineAlgorithm": 'on'
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(
			Path(__neoMetaModel__._omfDir, "static", "publicFeeders", defaultInputs["feederName1"]+'.omd'),
			Path(modelDir, defaultInputs["feederName1"]+'.omd'))
		shutil.copyfile( meter_file_path, Path(modelDir, meter_file_name) )
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

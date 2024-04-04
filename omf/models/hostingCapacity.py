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
import matplotlib.pyplot as plt


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

def bar_chart_coloring( row ):
	color = 'black'
	if row['thermal_violation'] and not row['voltage_violation']:
		color = 'orange'
	elif not row['thermal_violation'] and row['voltage_violation']:
		color = 'yellow'
	elif not row['thermal_violation'] and not row['voltage_violation']:
		color = 'green'
	else:
		color = 'red'
	return color

def createColorCSV(modelDir, df):
	new_df = df[['bus','max_kw']]
	new_df.to_csv(Path(modelDir, 'color_by.csv'), index=False)

def my_GetCoords(dssFilePath):
	'''Takes in an OpenDSS circuit definition file and outputs the bus coordinates as a dataframe.'''
	dssFileLoc = os.path.dirname(dssFilePath)
	curr_dir = os.getcwd()
	opendss.runDSS(dssFilePath)
	opendss.runDssCommand(f'export buscoords "{curr_dir}/coords.csv"')
	coords = pd.read_csv(curr_dir + '/coords.csv', header=None)
	# JENNY - Deleted Radius and everything after.
	coords.columns = ['Element', 'X', 'Y']
	return coords
	
def omd_to_nx( dssFilePath, tree=None ):
	''' Combines dss_to_networkX and opendss.networkPlot together.

	Creates a networkx directed graph from a dss files. If a tree is provided, build graph from that instead of the file.
	Creates a .png picture of the graph.
	Adds data to certain DSS node types ( loads )
	
	args:
		filepath (str of file name):- dss file path
		tree (list): None - tree representation of dss file
		output_name (str):- name of png
		show_labels (bool): true - show node label names
		node_size (int): 300 - size of node circles in png
		font_size (int): 8 - font size for png labels
	return:
		A networkx graph of the circuit 
	'''
	if tree == None:
		tree = opendss.dssConvert.dssToTree( dssFilePath )

	G = nx.DiGraph()
	pos = {}

	setbusxyList = [x for x in tree if '!CMD' in x and x['!CMD'] == 'setbusxy']
	x_coords = [x['x'] for x in setbusxyList if 'x' in x]
	y_coords = [x['y'] for x in setbusxyList if 'y' in x]
	bus_names = [x['bus'] for x in setbusxyList if 'bus' in x]
	for bus, x, y in zip( bus_names, x_coords, y_coords):
		G.add_node(bus, pos=(x, y))
		pos[bus] = (x, y)

	lines = [x for x in tree if x.get('object', 'N/A').startswith('line.')]
	bus1_lines = [x.split('.')[0] for x in [x['bus1'] for x in lines if 'bus1' in x]]
	bus2_lines = [x.split('.')[0] for x in [x['bus2'] for x in lines if 'bus2' in x]]
	edges = []
	for bus1, bus2 in zip( bus1_lines, bus2_lines):
		edges.append( (bus1, bus2) )
	G.add_edges_from(edges)

	# Need edges from bus --- trasnformr info ---> load
	transformers = [x for x in tree if x.get('object', 'N/A').startswith('transformer.')]
	transformer_bus_names = [x['buses'] for x in transformers if 'buses' in x]
	bus_to_transformer_pairs = {}
	for transformer_bus in transformer_bus_names:
		strip_paren = transformer_bus.strip('[]')
		split_buses = strip_paren.split(',')
		bus = split_buses[0].split('.')[0]
		transformer_name = split_buses[1].split('.')[0]
		bus_to_transformer_pairs[transformer_name] = bus
	
	loads = [x for x in tree if x.get('object', 'N/A').startswith('load.')] # This is an orderedDict
	load_names = [x['object'].split('.')[1] for x in loads if 'object' in x and x['object'].startswith('load.')]
	load_transformer_name = [x.split('.')[0] for x in [x['bus1'] for x in loads if 'bus1' in x]]

	# Connects loads to buses via transformers
	labels = {}
	for load_name, load_transformer in zip(load_names, load_transformer_name):
    # Add edge from bus to load, with transformer name as an attribute
		bus = bus_to_transformer_pairs[load_transformer]
		G.add_edge(bus, load_name, transformer=load_transformer)
		pos[load_name] = pos[load_transformer]
		labels[load_name] = load_name
		labels[ bus ] = bus
	
	# TEMP: Remove transformer nodes added from coordinates. Transformer data is edges, not nodes.
	for transformer_name in load_transformer_name:
		if transformer_name in G.nodes:
			G.remove_node( transformer_name )
			pos.pop( transformer_name )
	
	load_kw = [x['kw'] for x in loads if 'kw' in x]
	for load, kw in zip( load_names, load_kw ):
		G.nodes[load]['kw'] = kw
	
	return [G, pos, labels]

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

def run_downline_load_algorithm( modelDir, inputDict, outData):
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd') and x[:-4] == inputDict['feederName1'] ][0]
	inputDict['feederName1'] = feederName[:-4]
	path_to_omd = Path(modelDir, feederName)
	tree = opendss.dssConvert.omdToTree(path_to_omd)
	opendss.dssConvert.treeToDss(tree, Path(modelDir, 'downlineLoad.dss'))
	downline_start_time = time.time()
	graphData = omd_to_nx( os.path.join( modelDir, 'downlineLoad.dss') )
	graph = graphData[0]
	buses = opendss.get_all_buses( os.path.join( modelDir, 'downlineLoad.dss') )
	buses_output = {}
	kwFromGraph = nx.get_node_attributes(graph, 'kw')
	for bus in buses:
		if bus in graph.nodes:
			kwSum = 0
			get_dependents = sorted(nx.descendants(graph, bus))
			for dependent in get_dependents:
				if dependent in kwFromGraph.keys():
					kwSum += float(kwFromGraph[dependent])
			buses_output[bus] = kwSum
	downline_output = pd.DataFrame(list(buses_output.items()), columns=['busname', 'kw'] )
	downline_end_time = time.time()
	sorted_downlineDF = downline_output.sort_values(by='busname')

	buses_to_remove = ['eq_source_bus', 'bus_xfmr']
	indexes = []
	for bus in buses_to_remove:
		indexes.append( sorted_downlineDF[sorted_downlineDF['busname'] == bus].index )
	for i in indexes:
		sorted_downlineDF = sorted_downlineDF.drop(i)
	outData['downline_tableHeadings'] = downline_output.columns.values.tolist()
	outData['downline_tableValues'] = (list(sorted_downlineDF.itertuples(index=False, name=None)))
	outData['downline_runtime'] = convert_seconds_to_hms_ms( downline_end_time - downline_start_time )

def run_ami_algorithm(modelDir, inputDict, outData):
	# mohca data-driven hosting capacity
	inputPath = Path(modelDir, inputDict['AMIDataFileName'])
	inputAsString = inputPath.read_text()

	outputPath = Path(modelDir, 'AMI_output.csv')
	AMI_output = []

	try:
		csvValidateAndLoad(inputAsString, modelDir=modelDir, header=0, nrows=None, ncols=5, dtypes=[str, pd.to_datetime, float, float, float], return_type='df', ignore_nans=False, save_file=None, ignore_errors=False )
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

	AMI_results = AMI_output[0].rename(columns={'kW_hostable': 'voltage_cap_kW'})
	histogramFigure = px.histogram( AMI_results, x='voltage_cap_kW', template="simple_white", color_discrete_sequence=["MediumPurple"] )
	histogramFigure.update_layout(bargap=0.5)
	# TBD - Needs to be modified when the MoHCA algorithm supports calculating thermal hosting capacity
	min_value = 5
	max_value = 8
	AMI_results['thermal_cap_kW']  = np.random.randint(min_value, max_value + 1, size=len(AMI_results))

	AMI_results['max_cap_allowed_kW'] = np.minimum( AMI_results['voltage_cap_kW'], AMI_results['thermal_cap_kW'])
	barChartFigure = px.bar(AMI_results, x='busname', y=['voltage_cap_kW', 'thermal_cap_kW', 'max_cap_allowed_kW'], barmode='group', color_discrete_sequence=["green", "lightblue", "MediumPurple"], template="simple_white" )
	barChartFigure.add_traces( list(px.line(AMI_results, x='busname', y='max_cap_allowed_kW', markers=True).select_traces()) )
	outData['histogramFigure'] = json.dumps( histogramFigure, cls=py.utils.PlotlyJSONEncoder )
	outData['barChartFigure'] = json.dumps( barChartFigure, cls=py.utils.PlotlyJSONEncoder )
	outData['AMI_tableHeadings'] = AMI_results.columns.values.tolist()
	outData['AMI_tableValues'] = ( list(AMI_results.sort_values( by="max_cap_allowed_kW", ascending=False, ignore_index=True ).itertuples(index=False, name=None)) )
	outData['AMI_runtime'] = convert_seconds_to_hms_ms( AMI_end_time - AMI_start_time )

def run_traditional_algorithm(modelDir, inputDict, outData):
	# traditional hosting capacity if they uploaded an omd circuit file and chose to use it.
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd') and x[:-4] == inputDict['feederName1'] ][0]
	inputDict['feederName1'] = feederName[:-4]
	path_to_omd = Path(modelDir, feederName)
	tree = opendss.dssConvert.omdToTree(path_to_omd)
	opendss.dssConvert.treeToDss(tree, Path(modelDir, 'circuit.dss'))
	traditional_start_time = time.time()
	traditionalHCResults = opendss.hosting_capacity_all(Path(modelDir, 'circuit.dss'), int(inputDict["traditionalHCMaxTestkw"]))
	traditional_end_time = time.time()
	# - opendss.hosting_capacity_all() changes the cwd, so change it back so other code isn't affected
	tradHCDF = pd.DataFrame(traditionalHCResults)
	tradHCDF['plot_color'] = tradHCDF.apply ( lambda row: bar_chart_coloring(row), axis=1 )
	# Plotly has its own colors - need to map the "name" of given colors to theirs
	traditionalHCFigure = px.bar( tradHCDF, x='bus', y='max_kw', barmode='group', color='plot_color', color_discrete_map={ 'red': 'red', 'orange': 'orange', 'green': 'green', 'yellow': 'yellow'}, template='simple_white' )
	traditionalHCFigure.update_xaxes(categoryorder='array', categoryarray=tradHCDF.bus.values)
	# Map color to violation type to update key/legend
	colorToKey = {'orange':'thermal_violation', 'yellow': 'voltage_violation', 'red': 'both_violation', 'green': 'no_violation'}
	# Changes the hover mode, key, and legend to show the violation type rather than the color
	traditionalHCFigure.for_each_trace(
		lambda t: t.update(
			name = colorToKey[t.name],
			legendgroup = colorToKey[t.name],
			hovertemplate = t.hovertemplate.replace(t.name, colorToKey[t.name])
			)
		)
	# We don't need the plot_color stuff for anything else, so drop it
	tradHCDF.drop(tradHCDF.columns[len(tradHCDF.columns)-1], axis=1, inplace=True)
	createColorCSV(modelDir, tradHCDF)
	attachment_keys = {
	"coloringFiles": {
		"color_by.csv": {
			"csv": "<content>",
			"colorOnLoadColumnIndex": "1"
		}
	}
	}
	data = Path(modelDir, 'color_by.csv').read_text()
	attachment_keys['coloringFiles']['color_by.csv']['csv'] = data
	omd = json.load(open(path_to_omd))
	new_path = Path(modelDir, 'color_test.omd')
	omd['attachments'] = attachment_keys
	with open(new_path, 'w+') as out_file:
		json.dump(omd, out_file, indent=4)
	omf.geo.map_omd(new_path, modelDir, open_browser=False )

	sorted_tradHCDF = tradHCDF.sort_values(by='bus')

	outData['traditionalHCMap'] = open(Path(modelDir, "geoJson_offline.html"), 'r' ).read()
	outData['traditionalGraphData'] = json.dumps(traditionalHCFigure, cls=py.utils.PlotlyJSONEncoder )
	outData['traditionalHCTableHeadings'] = tradHCDF.columns.values.tolist()
	outData['traditionalHCTableValues'] = (list(sorted_tradHCDF.itertuples(index=False, name=None)))
	outData['traditionalRuntime'] = convert_seconds_to_hms_ms( traditional_end_time - traditional_start_time )
	outData['traditionalHCResults'] = traditionalHCResults

def runtimeEstimate(modelDir):
	''' Estimated runtime of model in minutes. '''
	return 1.0

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	meter_file_name = 'mohcaInputCustom.csv'
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

''' Calculate hosting capacity using traditional and/or AMI-based methods. '''
import shutil
from os.path import join as pJoin
import plotly as py
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# OMF imports
import omf
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
from omf.solvers import opendss

# Model metadata:
tooltip = "Calculate hosting capacity using traditional and/or AMI-based methods."
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = False

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

def colorby( hc_color_dict ):
	''' generate a colorby CSV/JSON that works with omf.geo map interface.
	To use, set omd['attachments'] = function JSON output'''
	attachments_keys = {
		"coloringFiles": {
			"microgridColoring.csv": {
				"csv": "<content>",
				"colorOnLoadColumnIndex": "1" # color by default
			}
		}
	}
	hc_keys = hc_color_dict.keys()
	color_step = float(1/len(hc_keys))
	output_csv = 'bus,color\n'
	for i, hc_key in enumerate(hc_color_dict):
		my_color = i * color_step
		hc_ob = hc_color_dict[hc_key]
		all_items = hc_ob['loads'] + hc_ob['gen_obs_existing'] + [hc_ob['gen_bus']]
		for item in all_items:
			output_csv += item + ',' + str(my_color) + '\n'
	attachments_keys['coloringFiles']['hostingCapColoring.csv']['csv'] = output_csv
	return attachments_keys

def work(modelDir, inputDict):
	outData = {}
	# mohca data-driven hosting capacity
	import mohca_cl
	with open(pJoin(modelDir,inputDict['inputDataFileName']),'w', newline='') as pv_stream:
		pv_stream.write(inputDict['inputDataFileContent'])
	inputPath = pJoin(modelDir, inputDict['inputDataFileName'])
	outputPath = pJoin(modelDir, 'mohcaOutput.csv')
	mohcaOutput = []
	if inputDict[ "mohcaAlgorithm" ] == "sandia1":
		mohcaOutput = mohca_cl.sandia1( inputPath, outputPath )
	elif inputDict[ "mohcaAlgorithm" ] == "sandia2":
		mohcaOutput = mohca_cl.sandia2( inputPath, outputPath )
	else:
		errorMessage = "Algorithm name error"
		raise Exception(errorMessage)
	mohcaResults = mohcaOutput[0].rename(columns={'kW_hostable': 'voltage_cap_kW'})
	mohcaHistogramFigure = px.histogram( mohcaResults, x='voltage_cap_kW', template="simple_white", color_discrete_sequence=["MediumPurple"] )
	mohcaHistogramFigure.update_layout(bargap=0.5)
	barChartDF = mohcaResults
	barChartDF['thermal_cap'] = [7.23, 7.34, 7.45, 7.53, 7.24, 6.24, 7.424, 7.23 ]
	barChartDF['max_cap_kW'] = np.minimum( barChartDF['voltage_cap_kW'], barChartDF['thermal_cap'])
	mohcaBarChartFigure = px.bar(barChartDF, x='busname', y=['voltage_cap_kW', 'thermal_cap', 'max_cap_kW'], barmode='group', color_discrete_sequence=["green", "lightblue", "MediumPurple"], template="simple_white" ) 
	# traditional hosting capacity if they uploaded an omd circuit file and chose to use it.
	circuitFileStatus = inputDict.get('optionalCircuitFile', 0)
	if ( circuitFileStatus == 'on' ):
		feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0]
		inputDict['feederName1'] = feederName
		tree = opendss.dssConvert.omdToTree(pJoin(modelDir, feederName))
		opendss.dssConvert.treeToDss(tree, pJoin(modelDir, 'circuit.dss'))
		traditionalHCResults = opendss.hosting_capacity_all(pJoin(modelDir, 'circuit.dss'), int(inputDict["traditionalHCSteps"]), int(inputDict["traditionalHCkW"]))
		tradHCDF = pd.DataFrame(traditionalHCResults)
		tradHCDF['plot_color'] = tradHCDF.apply ( lambda row: bar_chart_coloring(row), axis=1 )
		traditionalHCFigure = px.bar( tradHCDF, x='bus', y='max_kw', barmode='group', color='plot_color', color_discrete_map={ 'red': 'red', 'orange': 'orange', 'green': 'green', 'yellow': 'yellow'}, template='simple_white' )
		traditionalHCFigure.update_xaxes(categoryorder='array', categoryarray=tradHCDF.bus.values)
		colorToKey = {'orange':'thermal_violation', 'yellow': 'voltage_violation', 'red': 'both_violation', 'green': 'no_violation'}
		traditionalHCFigure.for_each_trace(lambda t: t.update(name = colorToKey[t.name],
                                      legendgroup = colorToKey[t.name],
                                      hovertemplate = t.hovertemplate.replace(t.name, colorToKey[t.name])
                                     )
                  )
		tradHCDF.drop(tradHCDF.columns[len(tradHCDF.columns)-1], axis=1, inplace=True)
		omf.geo.map_omd(pJoin(modelDir, feederName), modelDir, open_browser=False )
		outData['traditionalHCMap'] = open( pJoin( modelDir, "geoJson_offline.html"), 'r' ).read()
		outData['traditionalGraphData'] = json.dumps( traditionalHCFigure, cls=py.utils.PlotlyJSONEncoder )
		outData['traditionalHCTableHeadings'] = tradHCDF.columns.values.tolist()
		outData['traditionalHCTableValues'] = ( list( tradHCDF.itertuples(index=False, name=None)))
	# write final outputs
	outData['stdout'] = "Success"
	outData['stderr'] = ""
	outData['mohcaHistogramFigure'] = json.dumps( mohcaHistogramFigure, cls=py.utils.PlotlyJSONEncoder )
	outData['mohcaBarChartFigure'] = json.dumps( mohcaBarChartFigure, cls=py.utils.PlotlyJSONEncoder )
	outData['mohcaHCTableHeadings'] = mohcaResults.columns.values.tolist()
	outData['mohcaHCTableValues'] = ( list(mohcaResults.sort_values( by="voltage_cap_kW", ascending=False, ignore_index=True ).itertuples(index=False, name=None)) ) #NOTE: kW_hostable
	return outData

def runtimeEstimate(modelDir):
	''' Estimated runtime of model in minutes. '''
	return 0.5

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	meter_file_name = 'mohcaInputCustom.csv'
	meter_file_path = pJoin(omf.omfDir,'static','testFiles', meter_file_name)
	meter_file_contents = open(meter_file_path).read()
	defaultInputs = {
		"modelType": modelName,
		"mohcaAlgorithm": 'sandia1',
		"inputDataFileName": meter_file_name,
		"inputDataFileContent": meter_file_contents,
		"feederName1": 'ieee37.dss',
		"traditionalHCSteps": 10,
		"optionalCircuitFile": 'on',
		"traditionalHCkW": 1
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(
			pJoin(__neoMetaModel__._omfDir, "static", "publicFeeders", defaultInputs["feederName1"]+'.omd'),
			pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
	except:
		return False
	return creationCode

@neoMetaModel_test_setup
def _disabled_tests():
	# Location
	modelLoc = pJoin(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
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

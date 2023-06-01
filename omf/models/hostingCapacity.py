''' Calculate solar photovoltaic system output using PVWatts. '''

import base64
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
from omf.models import derInterconnection

# Model metadata:
tooltip = "The hostingCapacity model calculates the kW hosting capacity available at each meter in the provided AMI data."
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = False

def work(modelDir, inputDict):
    outData = {}
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
    mohcaHistogramFigure.update_layout(  bargap=0.5, title=dict(text="Mohca Hosting Capacity Distribution", font=dict(size=20) ) )

    barChartDF = mohcaResults
    barChartDF['thermal_cap'] = [1]
    barChartDF['max_cap_kW'] = np.minimum( barChartDF['voltage_cap_kW'], barChartDF['thermal_cap'])

    mohcaBarChartFigure = px.bar(barChartDF, x='busname', y=['voltage_cap_kW', 'thermal_cap', 'max_cap_kW'], barmode='group', color_discrete_sequence=["green", "lightblue", "MediumPurple"], template="simple_white" ) 
    mohcaBarChartFigure.update_layout( title=dict(text="Hosting Capacity by Bus", font=dict(size=20) ) )

    # Line graph of the data
    # timeSeriesFigure = px.line( mohcaResults.sort_values( by="kW_hostable", ascending=False, ignore_index=True ), x='busname', y='kW_hostable', markers=True, color_discrete_sequence=['purple', "blue", "green"])
    # timeSeriesFigure.update_yaxes(rangemode="tozero") # This line sets the base of the y axis to be 0.

    # traditional hosting capacity
    # if they uploaded an omd circuit file
    circuitFileStatus = inputDict.get('optionalCircuitFile', 0)
    if ( circuitFileStatus == 'on' ):
      feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0]
      inputDict['feederName1'] = feederName

      omd = json.load(open( pJoin( modelDir, inputDict['feederName1']) ))
      tree = omd.get('tree',{})
      #for k, v in omd['tree'].items():

      # once we take the omd file and convert it to a tree, we can loop through the objects to find all the 'bus' objects, that can be our second input
      # then there are option inputs for the step and kw for the user to put in? idk
      # print( os.path.abspath(feederName) ) why is this in the omf directory and not the modelDir?
      traditionalHCResults = omf.solvers.opendss.hosting_capacity_verbose(feederName, ['701', '730', '703', '724'], int( inputDict["traditionalHCSteps"] ), int( inputDict["traditionalHCkW"] ), modelDir )
      tradHCDF = traditionalHCResults[0]
      print( tradHCDF )

      filename = os.path.basename(inputDict['feederName1'])
      omdInput = pJoin( modelDir, filename )
      omf.geo.map_omd( omdInput, modelDir, open_browser=False )
      # outData['traditionalHCMap'] = pJoin( modelDir, 'geoJson_offline.html')
      outData['traditionalHCMap'] = open( pJoin( modelDir, "geoJson_offline.html"), 'r' ).read()

      traditionalHCFigure = make_subplots(specs=[[{"secondary_y": True }]])
      traditionalHCFigure.add_trace(
        go.Scatter( x = tradHCDF.index, y = tradHCDF["kw_add"], name= "kw_add"),
        secondary_y=False
      )
      traditionalHCFigure.add_trace(
        go.Scatter( x = tradHCDF.index, y = tradHCDF["v_max_pu1"], name= "v_max_pu1"),
        secondary_y=True
      )
      traditionalHCFigure.add_trace(
        go.Scatter( x = tradHCDF.index, y = tradHCDF["v_max_pu2"], name= "v_max_pu2"),
        secondary_y=True
      )
      traditionalHCFigure.add_trace(
        go.Scatter( x = tradHCDF.index, y = tradHCDF["v_max_pu3"], name= "v_max_pu3"),
        secondary_y=True
      )
      traditionalHCFigure.add_trace(
        go.Scatter( x = tradHCDF.index, y = tradHCDF["v_max_all_pu"], name= "v_max_all_pu"),
        secondary_y=True
      )
      traditionalHCFigure.update_yaxes( title_text="<b>Voltage ( PU )</b>", secondary_y = False)
      traditionalHCFigure.update_yaxes( title_text="<b>Total Additional Generation Added ( kW ) </b>", secondary_y = True)
      outData['traditionalGraphData'] = json.dumps( traditionalHCFigure, cls=py.utils.PlotlyJSONEncoder )
      outData['traditionalHCTableHeadings'] = traditionalHCResults[0].columns.values.tolist()
      outData['traditionalHCTableValues'] = ( list( traditionalHCResults[0].itertuples(index=False, name=None)))

    # Stdout/stderr.
    outData['stdout'] = "Success"
    outData['stderr'] = ""
    outData['mohcaHistogramFigure'] = json.dumps( mohcaHistogramFigure, cls=py.utils.PlotlyJSONEncoder )
    outData['mohcaBarChartFigure'] = json.dumps( mohcaBarChartFigure, cls=py.utils.PlotlyJSONEncoder )
    outData['mohcaHCTableHeadings'] = mohcaResults.columns.values.tolist()
    outData['mohcaHCTableValues'] = ( list(mohcaResults.sort_values( by="voltage_cap_kW", ascending=False, ignore_index=True ).itertuples(index=False, name=None)) ) #NOTE: kW_hostable
    
    # Stdout/stderr.
    outData['stdout'] = "Success"
    outData['stderr'] = ""
    return outData

def runtimeEstimate(modelDir):
    ''' Estimated runtime of model in minutes. '''
    return 0.5

def new(modelDir):
    ''' Create a new instance of this model. Returns true on success, false on failure. '''
    test_file_name = 'sandia_loc1_test_data.csv'
    test_file_path = pJoin(omf.omfDir,'static','testFiles', test_file_name)
    test_circuit_name = "ieee37_LBL"
    test_file_contents = open(test_file_path).read()
    defaultInputs = {
        "dataVariableName": 'None',
        "mohcaAlgorithm": 'sandia1',
        "feederName1": test_circuit_name,
        "inputDataFileName": test_file_name,
        "inputDataFileContent": test_file_contents,
        "modelType": modelName,
        "traditionalHCSteps": 10,
        "optionalCircuitFile": 'on',
        "traditionalHCkW": 1
    }
    creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
    try:
      shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "static", "hostingcapacityfiles", defaultInputs["feederName1"]+'.omd'), pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
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
        # No previous test results.
        pass
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

''' Calculate solar photovoltaic system output using PVWatts. '''

import shutil
from os.path import join as pJoin
import plotly as py
import plotly.express as px
import pandas as pd
import numpy as np

# OMF imports
import omf
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *

# Model metadata:
tooltip = "The hostingCapacity model calculates the kW hosting capacity available at each meter in the provided AMI data."
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = False

def csvBusSplitter( modelDir, inputCSVFile ):
    '''
    Splits input CSV wtih multiple buses and data to separate CSV's for each unique bus
    args: modelDir, CSV file to split
    return:
    - busFiles: the output CSV files of each separated bus
    - busNames: list of unique bus names
    '''
    busFiles = []
    df_dict = dict()
    busNames = []
    df_inputs = pd.read_csv( inputCSVFile )
    busNames = df_inputs.busname.unique().tolist()
    if ( np.size( busNames ) == 1 ): # if there's only 1 bus
        busFiles.append( inputCSVFile)
    else:
        for busname in busNames:
            df_dict[busname] = df_inputs[df_inputs['busname'] == busname]

        for df in df_dict:
            busFileName = pJoin( modelDir, df + "_mohca_input_file" )
            busFiles.append( busFileName )
            df_dict[df].to_csv( busFileName,  index=False )

    return [busFiles, busNames]

def work(modelDir, inputDict):

    import mohca_cl
    
    # Writing the content from the input into a file for the mohca algorithm to read in.
    with open(pJoin(modelDir,inputDict['inputDataFileName']),'w', newline='') as pv_stream:
        pv_stream.write(inputDict['inputDataFileContent'])
    
    inputPath = pJoin(modelDir, inputDict['inputDataFileName'])
    outputPath = pJoin(modelDir, 'mohcaOutput.csv')

    mohcaOutput = []
    if ( inputDict[ "mohcaAlgorithm" ] == "sandia1" ):
       mohcaOutput = mohca_cl.sandia1( inputPath, outputPath )
    elif (inputDict[ "mohcaAlgorithm" ] == "sandia2"):
       mohcaOutput = mohca_cl.sandia2( inputPath, outputPath )
    else:
       errorMessage = "Algorithm name error"
       raise Exception(errorMessage)
    
    # This was written when the sandia algorithm does not support multiple buses
    # multipleBusOutput = csvBusSplitter( modelDir, inputPath )
    # inputPaths = multipleBusOutput[0]
    # busNames = multipleBusOutput[1]

    # mohcaOutput = []
    # for i in range( len(busNames) ):
    #     outputPath = pJoin( modelDir, busNames[i] + "_mohca_output_file")
    #     if ( inputDict[ "mohcaAlgorithm" ] == "sandia1" ):
    #         mohcaOutput.append( (mohca_cl.sandia1( inputPaths[i], outputPath ))[0] )
    #     elif (inputDict[ "mohcaAlgorithm" ] == "sandia2"):
    #         mohcaOutput.append( (mohca_cl.sandia2( inputPaths[i], outputPath ))[0] )
    #     else:
    #         errorMessage = "Algorithm name error"
    #         raise Exception(errorMessage)
    # allOutputs = pd.concat( mohcaOutput )
    
    # post busSplitting
    mohcaResults = mohcaOutput[0]
    columnChartFigure = px.histogram(mohcaResults, x='busname', y='kW_hostable', color='kW_hostable', color_discrete_sequence=['purple', "blue", "green"] ) 
    timeSeriesFigure = px.line( mohcaResults.sort_values( by="kW_hostable", ascending=False, ignore_index=True ), x='busname', y='kW_hostable', markers=True, color_discrete_sequence=['purple', "blue", "green"])
    # timeSeriesFigure.update_yaxes(rangemode="tozero") # This line sets the base of the y axis to be 0.

    # traditional hosting capacity
    # ATM 2 issues
    # - don't know what inputs to put in for the traditional hosting capacity function
    # - when attempting to run the function with guessing inputs,
    test_dss_file = pJoin(omf.omfDir, 'static', 'hostingcapacityfiles', 'ieee37_LBL.dss')
    # look at second val of results tuple
    # traditionalHCresults = omf.solvers.opendss.hosting_capacity(test_dss_file, ['701', '730', '703', '724'], 1, 6.5)

    outData = {}
    # Stdout/stderr.
    outData['stdout'] = "Success"
    outData['stderr'] = ""
    outData['columnChartData'] = json.dumps( columnChartFigure, cls=py.utils.PlotlyJSONEncoder )
    outData['timeSeriesData'] = json.dumps( timeSeriesFigure, cls=py.utils.PlotlyJSONEncoder )
    outData['mohcaHCTableHeadings'] = mohcaResults.columns.values.tolist()
    outData['mohcaHCTableValues'] = ( list(mohcaResults.sort_values( by="kW_hostable", ascending=False, ignore_index=True ).itertuples(index=False, name=None)) )
    outData['traditionalHCTableHeadings'] = traditionalHCresults[0].columns.values.tolist()
    outData['traditionalHCTableValues'] = ( list( traditionalHCresults[0].itertuples(index=False, name=None)))
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
    test_file_path = pJoin(omf.omfDir,'static','testFiles',test_file_name)
    test_file_contents = open(test_file_path).read()
    test_omd_file = pJoin(omf.omfDir, 'static', 'hostingcapacityfiles', 'ieee37_LBL.omd')
    defaultInputs = {
        "dataVariableName": 'None',
        "feederName1": "ieee37_LBL",
        "inputDataFileName": test_file_name,
        "inputDataFileContent": test_file_contents,
        "modelType": modelName,
        "mohcaAlgorithm": 'None'
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

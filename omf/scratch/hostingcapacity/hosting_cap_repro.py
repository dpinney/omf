import omf
from pathlib import Path
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
from omf.solvers import opendss
from omf.solvers import mohca_cl
import time

meter_file_name = 'mohcaInputCustom.csv'
meter_file_path = Path(omf.omfDir,'static','testFiles', 'hostingCapacity', meter_file_name)
modeldir = Path(omf.omfDir, 'scratch', 'hostingCapacity')

#  2541.865383386612  - iowa state 
def run_ami_algorithm(modelDir, meterfileinput, outData):
	# mohca data-driven hosting capacity
	inputPath = Path(modelDir, meterfileinput)
	outputPath = Path(modelDir, 'AMI_output.csv')
	AMI_start_time = time.time()
	AMI_output = mohca_cl.sandia1( inputPath, outputPath )
	AMI_end_time = time.time()
	runtime = AMI_end_time - AMI_start_time
	return runtime


def convert_seconds_to_hms_ms(seconds):
    # Convert seconds to milliseconds
    milliseconds = seconds * 1000
    
    # Calculate hours, minutes, seconds, and milliseconds
    hours, remainder = divmod(milliseconds, 3600000) # 3600000 milliseconds in an hour
    minutes, remainder = divmod(remainder, 60000)    # 60000 milliseconds in a minute
    seconds, milliseconds = divmod(remainder, 1000) # 1000 milliseconds in a second
    
    # Format the output
    return "{:02d}:{:02d}:{:02d}.{:03d}".format(int(hours), int(minutes), int(seconds), int(milliseconds))
	
runtime = run_ami_algorithm(modeldir, meter_file_path, 'output.csv')
print( 'AMI_runtime: ', runtime)
print( 'formatted time: ', convert_seconds_to_hms_ms( runtime ))
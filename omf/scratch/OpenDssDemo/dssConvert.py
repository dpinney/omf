# Prereq: `pip install 'git+https://github.com/NREL/ditto.git@master#egg=ditto[all]'`
import os
import sys
from ditto.store import Store
from ditto.readers.opendss.read import Reader as dReader
from ditto.writers.opendss.write import Writer as dWriter
from ditto.readers.gridlabd.read import Reader as gReader
from ditto.writers.gridlabd.write import Writer as gWriter

def gridLabToDSS(inFile):
	''' Convert gridlab file to dss. ''' 
	model = Store()
	# HACK: the gridlab reader can't handle brace syntax that ditto itself  writes...
	# command = 'sed -i -E "s/(\\w)\\{/\\1 \\{/" ' + inFile
	# os.system(command)
	gld_reader = gReader(input_file = inFile)
	gld_reader.parse(model)
	model.set_names()
	dss_writer = dWriter(output_path=".")
	dss_writer.write(model)

def dssToGridLab(inFile, busCoords=None):
	''' Convert dss file to gridlab. '''
	model = Store()
	dss_reader = dReader(master_file = inFile)
	dss_reader.parse(model)
	model.set_names()
	glm_writer = gWriter(output_path=".")
	glm_writer.write(model)

if __name__ == '__main__':
	dssToGridLab('ieee37.dss')
	gridLabToDSS('Model.glm')
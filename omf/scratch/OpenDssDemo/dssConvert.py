# Prereq: `pip install 'git+https://github.com/NREL/ditto.git@master#egg=ditto[all]'`
import os
import sys
from ditto.store import Store
from ditto.readers.opendss.read import Reader as dReader
from ditto.writers.opendss.write import Writer as dWriter
from ditto.readers.gridlabd.read import Reader as gReader
from ditto.writers.gridlabd.write import Writer as gWriter

def gridLabToDSS(inFilePath, outFilePath):
	''' Convert gridlab file to dss. ''' 
	model = Store()
	# HACK: the gridlab reader can't handle brace syntax that ditto itself  writes...
	# command = 'sed -i -E "s/(\\w)\\{/\\1 \\{/" ' + inFilePath
	# os.system(command)
	gld_reader = gReader(input_file = inFilePath)
	gld_reader.parse(model)
	model.set_names()
	dss_writer = dWriter(output_path=".")
	# TODO: no way to specify output filename, so move and rename.
	dss_writer.write(model)

def dssToGridLab(inFilePath, outFilePath, busCoords=None):
	''' Convert dss file to gridlab. '''
	model = Store()
	#TODO: do something about busCoords: 
	dss_reader = dReader(master_file = inFilePath)
	dss_reader.parse(model)
	model.set_names()
	glm_writer = gWriter(output_path=".")
	# TODO: no way to specify output filename, so move and rename.
	glm_writer.write(model)

def dssToTree(pathToDss):
	pass #TODO: implement

def treeToDss(treeObject):
	pass #TODO: implement

def schemaConvert(treeObject, kind):
	validKinds = ['DSS-to-GLD', 'GLD-to-DSS']
	if kind not in validKinds:
		raise Exception('Kind of conversion must be one of ' + str(validKinds))
	pass #TODO: maybe implement?

if __name__ == '__main__':
	dssToGridLab('ieee37.dss', 'Model.glm') # this kind of works
	# gridLabToDSS('Model.glm', 'ieee37-round-trip.dss') # this fails miserably
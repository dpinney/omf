import os
import sys
import argparse
from ditto.store import Store
from ditto.readers.gridlabd.read import Reader as GReader
from ditto.writers.gridlabd.write import Writer as GWriter
from ditto.readers.opendss.read import Reader as OReader
from ditto.writers.opendss.write import Writer as OWriter


def gridLabToDSS(args):
	''' Convert gridlab file to dss. ''' 
	m = Store()
	reader = GReader(input_file=args.infile)
	writer = GWriter(output_path='.')
	reader.parse(m)
	writer.write(m)
	print ("DSS FILE WRITTEN")

def dssToGridLab(args):
	''' Convert dss file to gridlab. '''
	m = Store()
	reader = OReader(master_file=args.infile, buscoordinates_file=args.buscoords)
	writer = Writer(output_path='.')
	reader.parse(m)
	writer.write(m)
	print ("GRIDLAB-D FILE WRITTEN")

def is_valid_file(filename):
	''' Make sure path is valid. ''' 
	if not os.path.exists(filename):
		parser.error("THE FILE %s DOES NOT EXIST" % filename)
	return

if __name__ == '__main__':
	
	# Use a dictionary to get different functions directly from command line arguments.
	function_map = {'gtd': gridLabToDSS, 'dtg': dssToGridLab}
	
	# Set up arg parse.
	parser = argparse.ArgumentParser()
	parser.add_argument("conversion", choices=function_map.keys())
	parser.add_argument("infile", help="input filename")
	parser.add_argument("--buscoords", help="input coordinates for DSS")
	args = parser.parse_args()
	# DSS files might require bus coordinates, for example.
	try:
		if args.conversion == 'dtg' and 'buscoords' not in vars(args):
			parser.error('REQUIRES BUS COORDINATES.')
		is_valid_file(args.infile)
		func = function_map[args.conversion]
		func(args)
	except KeyError:
		print ("CONVERSION NOT SUPPORTED BY SCRIPT.")
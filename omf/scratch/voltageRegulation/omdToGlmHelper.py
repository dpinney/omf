
import json, math, os, argparse
from omf import feeder
from os.path import join as pJoin
import pandas as pd
import numpy as np
import csv

parser = argparse.ArgumentParser(description='Converts an OMD to GLM and runs it on gridlabd')
parser.add_argument('file_path', metavar='base', type=str,
                    help='Path to OMD.')
args = parser.parse_args()
filePath = args.file_path

# def gridlabdOMD(filePath):
filePath = '/Users/tuomastalvitie/Desktop/UCS_Egan_Housed_Solar.omd'

data=json.load(open(filePath))

with open('outGLM.glm', 'w') as f:
	f.write(feeder.sortedWrite(data['tree']))
os.system('/Users/tuomastalvitie/utilitySimGB/gldcore/gridlabd /Users/tuomastalvitie/omf/omf/scratch/voltageRegulation/outGLM.glm')


data = pd.read_csv('voltDump.csv', skiprows=[0])

# print data.head()
# print list(data)

offenders = []
for i, row in data['voltA_real'].iteritems():
	voltA_real = data.loc[i,'voltA_real']
	voltA_imag = data.loc[i,'voltA_imag']
	voltA_mag = np.sqrt(np.add((voltA_real*voltA_real), (voltA_imag*voltA_imag)))
	voltB_real = data.loc[i,'voltB_real']
	voltB_imag = data.loc[i,'voltB_imag']
	voltB_mag = np.sqrt(np.add((voltB_real*voltB_real), (voltB_imag*voltB_imag)))
	voltC_real = data.loc[i,'voltC_real']
	voltC_imag = data.loc[i,'voltC_imag']
	voltC_mag = np.sqrt(np.add((voltC_real*voltC_real), (voltC_imag*voltC_imag)))
	if (voltA_mag or voltB_mag or voltC_real) > (1.05 * 14400):
		offenders.append(data['node_name'][i])

		
offenders = list(set(offenders))

with open('offenders.csv', 'w') as f:
	wr = csv.writer(f, quoting=csv.QUOTE_ALL)
	wr.writerow(offenders)

print offenders



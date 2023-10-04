import omf
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
from omf.solvers import opendss
import pathlib

def list_of_dicts_to_dataframe(list_of_dicts):
    ''' Does what the funciton name says. Make sure the dicts have consistent keys. '''
    return pd.DataFrame(list_of_dicts)

modelDir = pathlib.PurePath(omf.omfDir, 'scratch', 'mohca')

# Example of hosting capacity for all buses with loads, i.e. metered buses.
# fnameDSS = pathlib.PurePath(omf.omfDir, 'data', 'Model', 'admin', 'good work', 'circuit.dss')
fnameDSS = pathlib.PurePath(omf.omfDir, 'solvers', 'opendss', 'iowa240.clean.dss')
meter_buses = opendss.get_meter_buses(fnameDSS)
iowa_hosting_dss = opendss.hosting_capacity_all(fnameDSS, kwSTEPS=10, kwValue=10.0)
iowa_df = list_of_dicts_to_dataframe(iowa_hosting_dss)
print(iowa_df.head)

fnameOMDfromDSS = pathlib.PurePath( fnameDSS, pathlib.PurePath(modelDir, 'iowatest.omd' ))
fnameTestDSSfromOMD = pathlib.PurePath( modelDir, 'circuit.dss')

opendss.dssConvert.dssToOmd(fnameDSS, fnameOMDfromDSS)
tree = opendss.dssConvert.omdToTree(fnameOMDfromDSS)
opendss.dssConvert.treeToDss(tree, fnameTestDSSfromOMD)
meter_buses = opendss.get_meter_buses(fnameTestDSSfromOMD)
iowa_hosting = opendss.hosting_capacity_all(fnameTestDSSfromOMD, 10, 10.0, BUS_LIST=meter_buses)
iowa_df_omd = list_of_dicts_to_dataframe(iowa_hosting)
print(iowa_df_omd.head)

'''
fnameOMD = pathlib.PurePath(omf.omfDir, 'static', 'publicFeeders', 'iowa240c1.clean.dss.omd')
tree = opendss.dssConvert.omdToTree(fnameOMD)
opendss.dssConvert.treeToDss(tree, pathlib.PurePath(modelDir, 'circuit.dss'))
meter_buses = opendss.get_meter_buses('circuit.dss')
iowa_hosting = opendss.hosting_capacity_all('circuit.dss', 10, 10.0, BUS_LIST=meter_buses)
iowa_df = list_of_dicts_to_dataframe(iowa_hosting)
print( iowa_df.head )
'''
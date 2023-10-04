import omf
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
from omf.solvers import opendss
import pathlib
import pandas as pd
import numpy as np
import plotly.express as px

def list_of_dicts_to_dataframe(list_of_dicts):
    ''' Does what the funciton name says. Make sure the dicts have consistent keys. '''
    return pd.DataFrame(list_of_dicts)

modelDir = pathlib.PurePath(omf.omfDir, 'scratch', 'mohca')

'''
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

fnameOMD = pathlib.PurePath(omf.omfDir, 'static', 'publicFeeders', 'iowa240c1.clean.dss.omd')
tree = opendss.dssConvert.omdToTree(fnameOMD)
opendss.dssConvert.treeToDss(tree, pathlib.PurePath(modelDir, 'circuit.dss'))
meter_buses = opendss.get_meter_buses('circuit.dss')
iowa_hosting = opendss.hosting_capacity_all('circuit.dss', 10, 10.0, BUS_LIST=meter_buses)
iowa_df = list_of_dicts_to_dataframe(iowa_hosting)
print( iowa_df.head )
'''

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

fname_syracuse = pJoin('/home', 'jenny', 'Downloads', 'Wheatland_syracuse.dss')
meter_buses = opendss.get_meter_buses(fname_syracuse)
syracuse_hosting = opendss.hosting_capacity_all(fname_syracuse, 10, 10.0, BUS_LIST=meter_buses)
syracuse_df = list_of_dicts_to_dataframe(syracuse_hosting)
syracuse_df.to_csv('syracuse_output.csv')

syracuse_df['plot_color'] = syracuse_df.apply ( lambda row: bar_chart_coloring(row), axis=1 )
syracuse_figure = px.bar( syracuse_df, x='bus', y='max_kw', barmode='group', color='plot_color', color_discrete_map={ 'red': 'red', 'orange': 'orange', 'green': 'green'}, template='simple_white' )
syracuse_figure.update_xaxes(categoryorder='array', categoryarray=syracuse_df.bus.values)
colorToKey = {'orange':'thermal_violation', 'green': 'voltage_violation', 'red': 'both_violation'}
syracuse_figure.for_each_trace(lambda t: t.update(name = colorToKey[t.name],
                                legendgroup = colorToKey[t.name],
                                hovertemplate = t.hovertemplate.replace(t.name, colorToKey[t.name])
                                )
                  )
syracuse_figure.show()

# Windings Test
fname_shelley = pJoin('/home', 'jenny', 'Downloads', 'Wheatland_shelley.dss')
shelley_hosting = opendss.hosting_capacity_all('Wheatland_shelley.dss', 5, 10)
shelley_df = list_of_dicts_to_dataframe( shelley_hosting )
shelley_df.to_csv('shelley_output.csv')
print( shelley_df )

shelley_df['plot_color'] = shelley_df.apply ( lambda row: bar_chart_coloring(row), axis=1 )
shelley_figure = px.bar( shelley_df, x='bus', y='max_kw', barmode='group', color='plot_color', color_discrete_map={ 'red': 'red', 'orange': 'orange', 'green': 'green'}, template='simple_white' )
shelley_figure.update_xaxes(categoryorder='array', categoryarray=shelley_df.bus.values)
colorToKey = {'orange':'thermal_violation', 'green': 'voltage_violation', 'red': 'both_violation'}
shelley_figure.for_each_trace(lambda t: t.update(name = colorToKey[t.name],
                                legendgroup = colorToKey[t.name],
                                hovertemplate = t.hovertemplate.replace(t.name, colorToKey[t.name])
                                )
                  )
shelley_figure.show()
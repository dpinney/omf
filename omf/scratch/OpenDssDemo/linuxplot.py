from numpy import *
from matplotlib.collections import LineCollection
import pandas as pd
import opendssdirect as dss
import matplotlib.pyplot as pyplot

dss.run_command('Redirect IEEE37.dss')
col_names = ['Bus', 'X', 'Y']
coord = pd.read_csv('IEEE37_BusXY.csv', names=col_names)
bus_x, bus_y = coord.iloc[:, 1].values, coord.iloc[:, 2].values
x_start, x_end, y_start, y_end = [zeros(len(coord))] * 4
print dss.PDElements.Count()
print dss.Bus.NumNodes()
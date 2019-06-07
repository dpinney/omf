import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math, warnings
import traceback
from os.path import join as pJoin
from jinja2 import Template
from matplotlib import pyplot as plt
import matplotlib
from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx

from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
plt.switch_backend('Agg')

# OMF imports 
import omf.feeder as feeder
from omf.solvers import gridlabd

# dateutil imports
from dateutil import parser
from dateutil.relativedelta import *

tree = omf.feeder.parse('test_ieee37nodeFaultTester.glm')
for key in tree:
	print(tree[key].get('name',''))
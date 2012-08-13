#!/usr/bin/env python

import doeAnalysis as da
import copy
import datetime as dt

anaSpec = {'analysisName':'test1','tmy2name':'IL-CHICAGO.tmy2','feederName':'13 Node Reference Feeder','simLength':'10','simLengthUnits':'days'}


print runtimeEstimate(anaSpec)
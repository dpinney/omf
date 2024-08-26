from pathlib import Path
import time
import pandas as pd
import shutil

import omf
from omf.solvers import opendss
from omf.models import hostingCapacity

if __name__ == '__main__':
  modelDir = Path(omf.omfDir, 'scratch', 'hostingcapacity')
  feederName = Path( omf.omfDir, 'static', 'publicFeeders', 'iowa240.clean.dss.omd')

  path_to_omd = Path(modelDir, feederName)
  tree = opendss.dssConvert.omdToTree(path_to_omd)
  opendss.dssConvert.treeToDss(tree, Path(modelDir, 'circuit.dss'))
  # traditional_start_time = time.time()
  # traditionalHCResults = opendss.hosting_capacity_all( FNAME = Path(modelDir, 'circuit.dss'), max_test_kw=int(50000), BUS_LIST=['t_bus3002_l'], multiprocess=False)
  # traditional_end_time = time.time()
  # print( "No multiprocessing:- ", traditional_end_time-traditional_start_time)

  # multiprocessor false single output:  {'bus': 't_bus3002_l', 'max_kw': 26.125, 'reached_max': True, 'thermal_violation': False, 'voltage_violation': False}
  # line 460
  # noMP_df = pd.DataFrame(traditionalHCResults)
  # noMP_df.to_csv('noMP_outputs.csv')

  mp_start_time = time.time()
  trad_multiproc = opendss.hosting_capacity_all( FNAME = Path(modelDir, 'circuit.dss'), max_test_kw=int(50000), multiprocess=True)
  mp_end_time = time.time()
  # print( "Multiprocessing:- ", mp_end_time-mp_start_time)

  mp_df = pd.DataFrame( trad_multiproc )
  mp_df.to_csv('MP_outputs.csv')



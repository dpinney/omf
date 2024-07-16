from pathlib import Path, PosixPath
import time
import pandas as pd
import os

import omf
from omf.solvers import opendss
from omf.models import hostingCapacity

def run_trad( epri_file, modelDir ):
  tradHC = opendss.hosting_capacity_all( FNAME = epri_file, max_test_kw=50000, multiprocess=False)
  epri_df = pd.DataFrame( tradHC )
  epri_df.to_csv('epri_outputs.csv')

def create_testfile( modelDir: PosixPath ):

  monitor_names = []
  load_profiles = os.path.join(  modelDir, 'dsstestcircuit', 'Profiles' )
  master_dss_file = os.path.join( modelDir, 'dsstestcircuit', 'Master copy.DSS')

  with open( os.path.join( modelDir, 'dsstestcircuit', 'Master copy.DSS' ) ) as file:
    for line in file:
      opendss.runDssCommand( line )
  
  volt_df = pd.read_csv('volts.csv')

  # Need a meter at every load
  add_to_dss = ''
  for file in os.listdir(load_profiles):
    if file.endswith('.dbl'):
      load_file_name = Path(file).stem
      monitor_name = f'monitor-load-{load_file_name}'
      obj_loadshape = 'Loadshape'
      # need to get rid of the _P and _Q
      # don't know if this works. I deleted it with vim
      # load_file_name = load_file_name[:-2]
      add_to_dss += f'new object=monitor.{monitor_name} element={obj_loadshape}.{load_file_name} terminal=1 mode=6\n'
      monitor_names.append(monitor_name)

  add_to_dss += f'set mode=yearly stepsize=15m\n'
  add_to_dss += f'set number=1\n'
  add_to_dss += 'solve\n'
  for name in monitor_names:
    add_to_dss += f'export monitors monitorname={name}\n'
	# Write runner file and run.
  with open( os.path.join(modelDir, 'dsstestcircuit', 'Master copy.DSS'), 'a') as run_file:
    run_file.write(add_to_dss)

if __name__ == '__main__':
  epri_file = Path( omf.omfDir, 'solvers', 'opendss', 'epriSecondaryTestCircuit.clean.dss' )
  modelDir = Path(omf.omfDir, 'scratch', 'hostingcapacity')
  # run_trad( epri_file, modelDir )
  # create_testfile( modelDir )
  master_dss_file = os.path.join( modelDir, 'dsstestcircuit', 'Master copy.DSS')
  opendss.runDSS(master_dss_file)
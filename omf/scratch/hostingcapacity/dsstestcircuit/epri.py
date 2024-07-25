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
  master_dss_file = 'Master copy.DSS'

  with open( os.path.join( modelDir, 'dsstestcircuit', master_dss_file ) ) as file:
    for line in file:
      opendss.runDssCommand( line )
  # Need a meter at every load

  # vsource, isource, generator, load, capacitor, regcontrol.

  add_to_dss = ''
  for file in os.listdir(load_profiles):
    if file.endswith('.dbl'):
      load_file_name = Path(file).stem
      load_file_name = load_file_name[:-2].capitalize()
      monitor_name = f'monitor-load-{load_file_name}'
      obj_load = 'Load'
      add_to_dss += f'new object=monitor.{monitor_name} element={obj_load}.{load_file_name} terminal=1 mode=0\n'
      monitor_names.append(monitor_name)

  add_to_dss += f'set mode=yearly stepsize=15m\n'
  add_to_dss += f'set number=35040\n'
  add_to_dss += 'solve\n'
  for name in monitor_names:
    add_to_dss += f'export monitors monitorname={name}\n'
	# Write runner file and run.
  with open( os.path.join(modelDir, 'dsstestcircuit', 'Master copy.DSS'), 'a') as run_file:
    run_file.write(add_to_dss)

def run_testfile():
  with open( os.path.join( modelDir, 'dsstestcircuit', 'Master copy.DS' ) ) as file:
    for line in file:
      opendss.runDssCommand( line )

if __name__ == '__main__':
  epri_file = Path( omf.omfDir, 'solvers', 'opendss', 'epriSecondaryTestCircuit.clean.dss' )
  modelDir = Path(omf.omfDir, 'scratch', 'hostingcapacity')

  # run_trad( epri_file, modelDir )
  # create_testfile( modelDir )
  # run_testfile()
  # volt_df = pd.read_csv('volts.csv')
  test_df_load_1_1 = pd.read_csv(  os.path.join( modelDir, 'dsstestcircuit', 'SecondaryTestCircuit_Mon_monitor-load-load1_1_1.csv') )
  test_df_load_1_1['datetime'] = test_df_load_1_1.apply(lambda row: f"{row[0]}:{row[1]:.0f}Z", axis=1)
  # convert seconds to minutes
  # remove seconds
  # change the 0 before the . to be a fake date and then increment that fake date
  print( test_df_load_1_1.head)
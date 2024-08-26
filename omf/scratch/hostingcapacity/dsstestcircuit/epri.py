from pathlib import Path, PosixPath
import time
import pandas as pd
import os
from datetime import datetime, timedelta
import math

import omf
from omf.solvers import opendss
from omf.models import hostingCapacity

def run_trad( epri_file, modelDir ):
  tradHC = opendss.hosting_capacity_all( FNAME = epri_file, max_test_kw=50000, multiprocess=False)
  epri_df = pd.DataFrame( tradHC )
  epri_df.to_csv('epri_outputs.csv')

def create_testfile( modelDir: PosixPath):
  monitor_names = []
  load_profiles = os.path.join(  modelDir, 'dsstestcircuit', 'Profiles' )
  # Need a meter at every load
  # vsource, isource, generator, load, capacitor, regcontrol.
  add_to_dss = ''
  for file in os.listdir(load_profiles):
    if file.endswith('.dbl'):
      load_file_name = Path(file).stem
      load_file_name = load_file_name[:-2]
      monitor_name = f'monitor-load-{load_file_name}'
      obj_load = 'Load'
      add_to_dss += f'new object=monitor.{monitor_name} element={obj_load}.{load_file_name} terminal=1 mode=0\n'
      monitor_names.append(monitor_name)
  add_to_dss += f'set mode=duty stepsize=15m\n'
  add_to_dss += f'set number=35040\n'
  add_to_dss += 'solve\n'
  for name in monitor_names:
    add_to_dss += f'export monitors monitorname={name}\n'
	# Write runner file and run.
  # with open( os.path.join(modelDir, 'dsstestcircuit', 'Master copy.DSS'), 'a') as run_file:
  #   run_file.write(add_to_dss)
  return monitor_names

def setup_csv_with_voltage( monitor_names ):
  load_names = []
  list_of_dataframes = []
  for monitor in monitor_names:
    circuitName = 'SecondaryTestCircuit'
    monitor_csv_path = f'{circuitName}_Mon_{monitor}_1.csv'
    basename = monitor_csv_path.split('-')
    loadname = basename[-1][:-6]
    load_names.append(load_names)

    load_df = pd.read_csv( monitor_csv_path )
    load_df.drop(['t(sec)', 'VAngle1', 'V2','VAngle2','I1','IAngle1','I2','IAngle2'], axis=1, inplace=True)
    # Need to insert a starting row below the title. Take v reading from the first value to make it easier.
    starting_v1_reading = load_df.at[0, 'V1']
    start_time = "2022-01-01T00:00Z"
    starting_row = pd.DataFrame({'hour': start_time, 'V1': starting_v1_reading}, index=[0])
    load_df = pd.concat( [starting_row, load_df[:]] ).reset_index(drop=True)
    load_df['datetime'] = start_time
    for i in range( 1, len(load_df) ):
      previous = load_df.loc[i-1, 'datetime']
      incremented = datetime.fromisoformat( (previous.rstrip('Z')) ) + pd.Timedelta(minutes=15)
      load_df.at[i, 'datetime'] = incremented.strftime("%Y-%m-%dT%H:%MZ")

    load_df.drop(['hour'], axis=1, inplace=True)
    load_df.rename(columns={'V1': 'v_reading'}, inplace=True)

    load_df['busname'] = loadname
    order = ['busname', 'datetime', 'v_reading']
    load_df = load_df[order]
    # load_df.to_csv(f'{loadname}.csv', index=False)
    list_of_dataframes.append( load_df) 
  # combined_df = pd.concat( list_of_dataframes, ignore_index=True)
  # combined_df.to_csv('fulldata.csv', index=False)
  return list_of_dataframes



# This code was written in made and I pasted it into a function.
def get_kw_kvar( monitor_names ):
  load_names = []
  list_of_dataframes = []
  for monitor in monitor_names:
    circuitName = 'SecondaryTestCircuit'
    monitor_csv_path = f'{circuitName}_Mon_{monitor}_1.csv'
    basename = monitor_csv_path.split('-')
    loadname = basename[-1][:-6]
    load_names.append(load_names)

    load_df = pd.read_csv( monitor_csv_path )
    load_df.drop(['t(sec)', 'S2 (kVA)', 'Ang2'], axis=1, inplace=True)
    for i in range( 0, len(load_df) ):
    # kW = kVA * cos (φ)
      load_df.at[i, 'kw_reading'] = load_df.at[i, 'S1 (kVA)'] * math.cos( math.radians( load_df.at[i, 'Ang1'] ) )
    # kVAR = kVA * sin(φ)
      load_df.at[i, 'kvar_reading'] = load_df.at[i, 'S1 (kVA)'] * math.sin( math.radians( load_df.at[i, 'Ang1'] ) )
    list_of_dataframes.append( load_df )
    # combined_df.drop(['hour', 'S1 (kVA)', 'Ang1'], axis=1, inplace=True)
    # combined_df = pd.concat( list_of_dataframes, ignore_index=True)
    # combined_df.to_csv('kw_kvar.csv', index=False)

  return list_of_dataframes

if __name__ == '__main__':
  epri_file_clean_dss = Path( omf.omfDir, 'solvers', 'opendss', 'epriSecondaryTestCircuit.clean.dss' )
  modelDir = Path(omf.omfDir, 'scratch', 'hostingcapacity')

  # run_trad( epri_file_clean_dss, modelDir )
  monitor_names = create_testfile( modelDir )
  # setup_csv_with_voltage( monitor_names=monitor_names )
  # opendss.runDSS('createTestSet.DSS')

  # kw_kvar_df = pd.read_csv( "kw_kvar.csv" )
  # fulldata_df = pd.read_csv( "fulldata.csv" )
  # need to add extra line to kw_kvar
  # need to add the csvs in a way where these are other columns
  # combined = pd.concat([fulldata_df, kw_kvar_df], axis=1, ignore_index=True)
  # combined.columns = ['busname', 'datetime', 'v_reading', 'kw_reading']
  # combined.to_csv("mohca_main.csv", index=False)

  mohca_dataset = pd.read_csv('doc - EPRI Secondary MoHCA test set.csv')

  # quartersize = int( len(mohca_dataset)/4 )
  # mohca_dataset_quarter = mohca_dataset.iloc[:quartersize]
  # mohca_dataset_otherquarter = mohca_dataset.iloc[quartersize:]
  # mohca_dataset_quarter.to_csv("mohca_dataset_quarter.csv", index=False)

  specific_loads = ['load1_1', 'load2_1', 'load3_1', 'load4_2', 'load5_3', 'load6_4', 'load7_1', 'load8_1', 'load9_1']
  filtered_df = mohca_dataset[mohca_dataset['busname'].isin(specific_loads)]
  filtered_df.to_csv('filtered_file.csv', index=False)

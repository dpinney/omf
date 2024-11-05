''' mohca_cl, command line interface to the Model-Free Hosting Capacity Algorithm. '''
import fire
from . import sandia
from . import ISU_PINNbasedHCA
import os
from pathlib import Path

mohca_dir = Path(__file__).parent

def add(x,y):
  ''' Add two python objects. Maybe ints, maybe floats, strings work... '''
  return x + y

def hello():
  ''' Hello world test function. '''
  return 'hello mohca'

def sandia1(in_path, out_path):
  ''' Execute Sandia hosting capacity algorithm on in_path CSV with output written as CSV to out_path. '''
  ret_value = sandia.hosting_cap(in_path, out_path)
  return ret_value

def iastate(in_path, out_path):
  ''' Execute ISU hosting capacity algorithm on in_path CSV with output written as CSV to out_path. '''
  ''' Besides the in_path and out_path, more setting information is needed for the code running. The information of the testing system is shown below.'''
  input_csv_path = 'ISU_InputData_realsystem.csv'  # input path
  output_csv_path = 'Output_csv_path.csv'      # output path
  system_name = 'AMU_EC3'                      # system name for model saving
  node_list_for_HC = [i for i in range(3)]     # selected bus for HC analysis
  total_bus_number = 50                        # total bus number
  model_retrain = 0                            # 1 for retraining; 0 for not training
  inverter_control_setting = 'var'             # two setting mode: var prioirty and watt priority
  inverter_advanced_control = 1                # 0->'without control'  1->'constant power factor' 2->'constant reactive power' 3->'active power-reactive power' 4->'voltage-reactive power'
  ret_value = ISU_PINNbasedHCA.PINN_HC(system_name, input_csv_path, output_csv_path, total_bus_number, nodes_selected=node_list_for_HC, retrain_indicator=model_retrain, inverter_control=inverter_advanced_control, control_setting=inverter_control_setting)
  #ret_value = ISU_PINNbasedHCA.PINN_HC(in_path, out_path)
  
  return ret_value

def run_all_tests():
  ''' Run all tests in the project. '''
  sandia.hosting_cap('./mohca_cl/test_data/loc1.csv', './mohca_cl/test_data/loc1_out.csv')
  sandia.sanity_check('./mohca_cl/test_data/HC_Results_model_based.csv', './mohca_cl/test_data/loc1_out.csv')

def init_cli():
  fire.Fire({
    'add': add,
    'hello': hello,
    'sandia1': sandia1,
    'run_all_tests': run_all_tests
  })

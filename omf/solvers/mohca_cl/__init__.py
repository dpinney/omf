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

def sandia2(in_path, out_path):
  return 'stub for lanl algo 2'

def gatech(in_path, out_path):
  return 'stub for GA tech algo'

def iastate(in_path, out_path):
  ''' Execute Sandia hosting capacity algorithm on in_path CSV with output written as CSV to out_path. '''
  ret_value = ISU_PINNbasedHCA.PINN_HC(in_path, out_path)
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
    'iastate': iastate,
    'gatech': gatech,
    'run_all_tests': run_all_tests
  })
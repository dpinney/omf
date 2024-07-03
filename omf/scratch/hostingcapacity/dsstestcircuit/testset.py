from pathlib import Path

# OMF imports
import omf
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
from omf.solvers import opendss
from omf.solvers import mohca_cl

def create_testfile():
  modelDir = Path(__file__).parent.resolve()

  with open( os.path.join( modelDir, "Master.DSS" ) ) as file:
    for line in file:
      opendss.runDssCommand( line )
  
  volt_df = pd.read_csv('volts.csv')

if __name__ == "__main__":
  create_testfile()
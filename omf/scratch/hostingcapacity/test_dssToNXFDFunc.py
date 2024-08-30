import unittest
from pathlib import Path
import os
import networkx as nx

# OMF Imports
import omf
from omf.solvers import opendss
from omf.models import hostingCapacity

print( "### Testing iowa240.clean.dss file on dss_to_nx_fulldata_function ###" )
modelDir = Path(omf.omfDir, 'scratch', 'hostingcapacity')
starting_omd_test_file = Path( omf.omfDir, 'static', 'publicFeeders', 'iowa240.clean.dss.omd')
tree = opendss.dssConvert.omdToTree( starting_omd_test_file )
opendss.dssConvert.treeToDss(tree, Path(modelDir, 'downlineLoad.dss'))
nx_data = opendss.dss_to_nx_fulldata( Path(modelDir, 'downlineLoad.dss') )
iowa240Graph = nx_data[0]
iowa240Pos = nx_data[1]

class Test_Iowa240_NX_Func( unittest.TestCase ):

  def test_sanity_check_bus_descendents_length(self):
    # Descendents for bus1002 in iowa240:
    # ['bus1003', 'bus1004', 'bus1005', 'bus1006', 'bus1007', 'bus1008', 'bus1009', 'bus1010', 'bus1011', 'bus1012',
    # 'bus1013', 'bus1014', 'bus1015', 'bus1016', 'bus1017', 'load_1003', 'load_1004', 'load_1005', 'load_1006', 'load_1007',
    # 'load_1008', 'load_1009', 'load_1010', 'load_1011', 'load_1012', 'load_1013', 'load_1014', 'load_1015', 'load_1016'
    # 'load_1017', 't_bus1003_l', 't_bus1004_l', 't_bus1005_l', 't_bus1006_l', 't_bus1007_l', 't_bus1008_l', 't_bus1009_l'
    # 't_bus1010_l', 't_bus1011_l', 't_bus1012_l', 't_bus1013_l', 't_bus1014_l', 't_bus1015_l', 't_bus1016_l', 't_bus1017_l']
    #  = 45
    self.assertEqual( len(sorted(nx.descendants(iowa240Graph, "bus1002"))), 45 )
  
  def test_sanity_check_load_data( self ):

    bus1_iowa240 = nx.get_node_attributes(iowa240Graph, 'bus1')
    phases_iowa240 = nx.get_node_attributes(iowa240Graph, 'phases')
    conn_iowa240 = nx.get_node_attributes(iowa240Graph, 'conn')
    kv_iowa240 = nx.get_node_attributes(iowa240Graph, 'kv')
    kw_iowa240 = nx.get_node_attributes(iowa240Graph, 'kw')
    kvar_iowa240 = nx.get_node_attributes(iowa240Graph, 'kvar')

    # new object=load.load_1006 bus1=t_bus1006_l.1.2 phases=1 conn=delta kv=0.208 kw=5.04 kvar=2.29629183968801
    self.assertEqual( bus1_iowa240['load_1006'], 't_bus1006_l' )
    self.assertEqual( int(phases_iowa240['load_1006']), 1 )
    self.assertEqual( conn_iowa240['load_1006'], 'delta' )
    self.assertEqual( float(kv_iowa240['load_1006']), 0.208 )
    self.assertEqual( float(kw_iowa240['load_1006']), 5.04 )
    self.assertEqual( float(kvar_iowa240['load_1006']), 2.29629183968801 )

if __name__ == "__main__":
  unittest.main()
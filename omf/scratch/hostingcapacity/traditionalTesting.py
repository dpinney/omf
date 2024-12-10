import pandas as pd
from pathlib import Path
import omf

modelDir = Path(omf.omfDir, 'scratch', 'hostingcapacity', )

bridgewater = Path(modelDir, 'bridgewater_latestandgreatest.dss' )
green = Path(modelDir, 'green_latestandgreatest.dss')
fairgrounds = Path(modelDir, 'fairgrounds_latestandgreatest.dss')

secondary = Path(omf.omfDir, 'solvers', 'opendss', 'epriSecondaryTestCircuit.clean.dss')

default = Path(omf.omfDir,'static', 'publicFeeders', 'iowa240.clean.dss.omd')
# tree = omf.solvers.opendss.dssConvert.omdToTree(default)
# omf.solvers.opendss.dssConvert.treeToDss(tree, Path(modelDir, 'circuit.dss'))
# omf.solvers.opendss.hosting_capacity_all( 'circuit.dss', 5000, BUS_LIST=[], multiprocess=False)

joes = Path(omf.omfDir, 'static', 'testFiles', 'hostingCapacity', 'input_secondaryTestCircuit.latestNgreatest.clean.dss')
# omf.solvers.opendss.hosting_capacity_all(FNAME=joes, BUS_LIST=['bussec7_01'])

#This half works.
#omf.solvers.opendss.hosting_capacity_all(FNAME=secondary, BUS_LIST=['bussec7_01'])

omf.solvers.opendss.hosting_capacity_all(FNAME=bridgewater, BUS_LIST=['20001525'])


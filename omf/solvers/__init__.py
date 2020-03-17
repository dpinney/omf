''' Container for all solvers. '''

import os
#import sys
#import re

# Make sure this module is on the path regardless of where its imported from.
_myDir = os.path.dirname(os.path.abspath(__file__))
#sys.path.append(_myDir)

# Grab all our submodules and include them whenever we include this package:
__all__ = [dirname if not dirname.endswith('.py') else dirname[:-3]
	for dirname in os.listdir(_myDir) if dirname not in
		[
			'__init__.py',
			'__pycache__',
			'gfm',
			'gridlabdv990',
			'matpower5.1',
			'matpower7.0'
			'nilmtk',
			'rdt',
			'.DS_Store'
		]
	]
# Import of all the sub-modules:
# ['gridlabd_gridballast', 'VB', 'saxSequitur', 'REopt', 'nrelsam2015', 'CSSS', 'nrelsam2013', 'SteinmetzController', 'gridlabd']
#for name in __all__:
#	exec('from . import ' + name)

# HACK: manual import for now due to incompatibility of Debian and NREL SAM 2015.
#from omf.solvers import gridlabd
#from omf.solvers import nrelsam2013

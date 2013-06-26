''' Run Gridlab. From a script. '''

import os, sys
os.chdir('..')
sys.path.append(os.getcwd())
import analysis, reports, studies

myAna = analysis.Analysis({})
studyList = []

#TODO: finish this.

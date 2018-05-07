import timeit
import os
import opendssdirect as dss

glm_input = 'powerflow_IEEE_37node.glm'
gridlab_sims = dict()

for i in range(1, 21):
  xlm_file = glm_input.replace('.glm', '.xml')
  os.system('gridlabd %s --output %s' % (glm_input, xlm_file))
  gridlab_sims[i] = xlm_file

'''
dss_sims = dict()

for j in range(1, 21):
  os.system('dss.run_command(%s)' % (str(file_path))
  dss_sims[j] = 
'''

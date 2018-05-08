import time
import psutil
import os
import opendssdirect as dss

def getMemory():
  process = psutil.Process(os.getpid())
  return process.memory_percent()

glm_input = 'powerflow_IEEE_37node.glm'
gridlab_sims = dict()

t = time.time()
for i in range(1, 21):
  os.system('gridlabd %s --verbose' % (glm_input))
  print "PROCESSED"

print 'TOTAL TIME: %f' % float((time.time()-t))
print 'AVG TIME: %f' % float((time.time()-t)/21.0)
print 'CPU PERCENTAGE: %f' % psutil.cpu_percent()
print 'MEMORY USAGE PERCENTAGE: %f' % getMemory()
'''
dss_sims = dict()

for j in range(1, 21):
  os.system('dss.run_command(%s)' % (str(file_path))
  dss_sims[j] = 
'''

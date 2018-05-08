import time
import psutil
import os
import opendssdirect as dss


def getGridlabMemory():
  process = psutil.Process(os.getpid())
  return process.memory_percent()

glm_input = 'powerflow_IEEE_37node.glm'
gridlab_sims = dict()

t1 = time.time()
for i in range(1, 21):
  os.system('gridlabd %s --verbose' % (glm_input))
  print "PROCESSED"

print 'TOTAL TIME: %f' % float((time.time()-t1))
print 'AVG TIME: %f' % float((time.time()-t1)/21.0)
print 'CPU PERCENTAGE: %f' % psutil.cpu_percent()
print 'MEMORY USAGE PERCENTAGE: %f' % getGridlabMemory()


t2 = time.time()
file_path = '../../../OpenDSS/Distrib/IEEETestCases/37Bus/ieee37.dss'
for j in range(1, 21):
  dss.run_command('Redirect ' + file_path)
  dss.run_command('Solve')
 

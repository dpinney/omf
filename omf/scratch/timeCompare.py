import time
import psutil
import os
import opendssdirect as dss

def getMemory():
  process = psutil.Process(os.getpid())
  return process.memory_percent()

glm_input = 'powerflow_IEEE_37node.glm'
gridlab_sims = dict()

t1 = time.time()
for i in range(1, 21):
  os.system('gridlabd %s --quiet' % (glm_input))

print 'TOTAL TIME FOR GRIDLAB: %f' % float(time.time()-t1)
print 'AVG TIME FOR GRIDLAB: %f' % float((time.time()-t1)/21.0)
print 'CPU USAGE PERCENTAGE FOR GRIDLAB: %f' % psutil.cpu_percent()
print 'MEMORY USAGE PERCENTAGE FOR GRIDLAB: %f' % getMemory()

print '\n\n\n'

t2 = time.time()


file_path = '../../../OpenDSS/Distrib/IEEETestCases/37Bus/ieee37.dss'
for j in range(1, 21):
  dss.run_command('Redirect ' + file_path)
  dss.run_command('Compile ' + file_path)

print 'TOTAL TIME FOR OPENDSS: %f' % float(time.time()-t2)
print 'AVG TIME FOR OPENDSS: %f' % float((time.time()-t2)/21.0)
print 'CPU USAGE PERCENTAGE FOR OPENDSS: %f' % psutil.cpu_percent()
print 'MEMORY USAGE PERCENTAGE FOR OPENDSS: %f' % getMemory()
print '\n'
print "FINISHED"

import subprocess

proc = subprocess.Popen('./gridlabd feeder.glm', stdout=subprocess.PIPE, shell=True)
(out, err) = proc.communicate()
'''
Start GRIP container, test the API endpoints.

TODO
XXX Docker build.
XXX Test interface.
XXX File handling backend and test.
XXX What routes? https://docs.google.com/presentation/d/17KTL5q3Nd8E_iUehLKGhCDZar8nkyn7hm8JOu6RMZ4Y/edit#slide=id.g389c95e613_0_15
OOO Implement routes.
'''

import os, webbrowser, omf

def docker_build():
	# Need to move files around to appease Docker's build model.
	os.chdir(omf.omfDir)
	os.system('cp scratch/GRIP/grip.Dockerfile .')
	# Build and restart container.
	os.system('docker build . -f grip.Dockerfile -t grip')
	os.system('docker stop grip_run')
	os.system('docker rm grip_run')
	os.system('docker run -d -p 5000:5000 --name grip_run grip')
	webbrowser.open_new('localhost:5000')
	# Cleanup.
	os.system('rm grip.py')
	os.system('rm grip.Dockerfile')

def docker_cleanup():
	os.system('docker stop grip_run')
	os.system('docker rm grip_run')

# Start the server.
import grip
from multiprocessing import Process
p = Process(target=grip.serve, args=())
p.start()
# Do a little testing.
import requests
# webbrowser.open_new('http://localhost:5000/eatfile')
response = requests.post('http://localhost:5000/eatfile', files={'test.txt':'NOTHING_TO_SEE_HERE\nMY_DUDE'})
print '##### RESPONSE STATUS CODE', response.status_code
# print 'YOOOOOOOOOOO', dir(response)
# print 'YOOOOOOOOOOO', response.text
# print 'YOOOOOOOOOOO', dir(response.raw)
print '##### RESPONSE CONTENT', response.content
# Block until the process terminates.
# p.join()
# I SUFFER. KILL ME.
p.terminate()
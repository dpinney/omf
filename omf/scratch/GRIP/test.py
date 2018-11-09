''' Start GRIP container, test the API endpoints. '''

import os, webbrowser

# Need to move files around to appease Docker's build model.
os.chdir('../../..')
os.system('cp omf/scratch/GRIP/grip.py omf/')
os.system('cp omf/scratch/GRIP/grip.Dockerfile .')
# Build and start container.
os.system('docker build . -f grip.Dockerfile -t grip')
os.system('docker stop grip_run')
os.system('docker rm grip_run')
os.system('docker run -d -p 5000:5000 --name grip_run grip')
webbrowser.open_new('localhost:5000')
# Cleanup.
os.system('rm omf/grip.py')
os.system('rm grip.Dockerfile')
# os.system('docker stop grip_run')
# os.system('docker rm grip_run')
import platform, os
# All installations require git to clone the omf
if platform.system() == 'Linux':
	# if Ubuntu run these commands:
	if platform.linux_distribution()[0]=="Ubuntu":
		# git clone https://github.com/dpinney/omf.git
		ubWorkDir = os.getcwd()
		os.system("sudo apt-get update")
		os.system("sudo apt-get install wget python-pip git unixodbc-dev libfreetype6-dev \
		pkg-config python-dev python-numpy alien python-pygraphviz \
		python-pydot ffmpeg mdbtools python-cairocffi python-tk")
		os.system("sudo apt-get install build-essential checkinstall")
		os.system("sudo apt-get install libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev")
		os.system("cd /usr/src")
		os.system("wget https://www.python.org/ftp/python/2.7.13/Python-2.7.13.tgz")
		os.system("tar xzf Python-2.7.13.tgz")
		os.system("cd Python-2.7.13")
		os.system("sudo ./configure")
		os.system("sudo make altinstall")
		os.system("cd " + ubWorkDir)
		os.system("wget https://sourceforge.net/projects/gridlab-d/files/gridlab-d/Last%20stable%20release/gridlabd-3.2.0-1.x86_64.rpm")
		os.system("sudo alien gridlabd-3.2.0-1.x86_64.rpm")
		workDir = os.getcwd()
		for file in os.listdir(workDir):
			if file.endswith('.deb'):
				debFile = file		
		os.system("sudo dpkg -i " + debFile)
		os.system("sudo apt-get install -f")
		os.system("cd omf")
		os.system("pip install -r requirements.txt")
		os.system("sudo python setup.py develop")
	# if CentOS 7 run these commands:
	elif platform.linux_distribution()[0]=="CentOS Linux":
		# git clone https://github.com/dpinney/omf.git
		centWorkDir = os.getcwd()
		os.system("sudo yum -y install wget git graphviz gcc xerces-c python-devel tkinter 'graphviz-devel.x86_64'")
		os.system("yum --enablerepo=extras install epel-release")
		os.system("sudo yum -y install mdbtools")
		os.system("sudo rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro")
		os.system("sudo rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-1.el7.nux.noarch.rpm")
		os.system("sudo yum -y install ffmpeg ffmpeg-devel -y")
		os.system("sudo yum -y install python-pip")
		os.system("wget --no-check-certificate https://sourceforge.net/projects/gridlab-d/files/gridlab-d/Last%20stable%20release/gridlabd-3.2.0-1.x86_64.rpm")
		os.system("rpm -Uvh gridlabd-3.2.0-1.x86_64.rpm")
		os.system("cd /usr/src")
		os.system("wget https://www.python.org/ftp/python/2.7.13/Python-2.7.13.tgz")
		os.system("tar xzf Python-2.7.13.tgz")
		os.system("cd Python-2.7.13")
		os.system("./configure")
		os.system("make altinstall")
		os.system("cd " + centWorkDir)
		os.system("cd omf")
		os.system("pip install -r requirements.txt")
		os.system("pip install --ignore-installed six")
		os.system("python setup.py develop")
# if Windows run these commands:
elif platform.system()=='Windows':
	# Need to manually download and install Python 2.7 and set python as a path variable, Git, Chocolatey 
	# Download Pygraphviz whl and place it in the omf directory
	# Use wget to download omf from github
	# git clone https://github.com/dpinney/omf.git
	workDir = os.getcwd()
	# chocoString = "@'%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe' -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command 'iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))' && SET 'PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin'"
	# os.system(chocoString)
	os.system("choco install -y git")
	os.system("choco install -y wget")
	os.system("choco install -y python2")
	os.system("choco install -y vcredist2008")
	os.system("choco install -y vcpython27")
	os.system("choco install -y ffmpeg")
	os.system("choco install -y graphviz")
	os.system("choco install -y pip")
	# Sometimes refreshenv doesnt properly update the path variables and pip doesnt work. 
	# Testing timeout and using refresh multiple times
	os.system("timeout 5")
	os.system("refreshenv")
	os.system("timeout 5")
	os.system("refreshenv")
	os.system("timeout 5")
	# Possible start a new process after refreshenv, maybe look for anothey way to refresh 
	# env variables in python
	# Manually setting path for pip and other scripts
	os.system('setx PATH "%PATH%;C:\Python27\Scripts')
	os.system("cd " + workDir)
	# Sometimes wget has a hard time downloading gridlabD
	if platform.architecture()[0] == '32bit':
		if 'gridlabd-3.2-win32.exe' not in os.listdir(workDir):	
			os.system("wget --no-check-certificate https://sourceforge.net/projects/gridlab-d/files/gridlab-d/Last%20stable%20release/gridlabd-3.2-win32.exe")
			os.system("gridlabd-3.2-win32.exe/silent")
		if 'pygraphviz-1.3.1-cp27-none-win32.whl' not in os.listdir(workDir):
			os.system("wget --no-check-certificate https://github.com/dpinney/omf/raw/master/omf/static/pygraphviz-1.3.1-cp27-none-win32.whl")
	elif platform.architecture()[1] == '64bit':
		# Note: has not been tested yet, only 32bit has
		if 'gridlabd-3.2-x64.exe' not in os.listdir(workDir):	
			os.system("wget --no-check-certificate https://sourceforge.net/projects/gridlab-d/files/gridlab-d/Last%20stable%20release/gridlabd-3.2-x64.exe")
			os.system("gridlabd-3.2-x64.exe/silent")
		if 'pygraphviz-1.3.1-cp27-none-win_amd64.whl' not in os.listdir(workDir):
			os.system("wget --no-check-certificate https://github.com/dpinney/omf/raw/master/omf/static/pygraphviz-1.3.1-cp27-none-win_amd64.whl")
	for file in os.listdir(workDir):
		if file.endswith('.whl'):
			whlFile = file
			os.system("pip install " + whlFile)
	os.system("cd omf")
	os.system("refreshenv")
	os.system("pip install -r requirements.txt")
	os.system("pip install setuptools==33.1.1")
	os.system("python setup.py develop")
# if Mac run these commands:
elif platform.system()=="Darwin":
	print 'Mac'
	# Install homebrew
	# os.system('/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"')
	# os.system('brew install wget python ffmpeg git graphviz')
	# os.system('brew link --overwrite python')
	# os.system('cd omf')
	# os.system('pip install -r requirements.txt')
	# os.system('python setup.py develop')

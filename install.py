import platform, os, sys


# Note: all installations require git to clone the omf first.
if platform.system() == "Linux" and platform.linux_distribution()[0] in ["Ubuntu","debian"]:
	os.system("sudo apt-get install python-pip git unixodbc-dev libfreetype6-dev \
	pkg-config python-dev python-numpy alien graphviz python-pygraphviz libgraphviz-dev \
	python-pydot mdbtools python-tk octave libblas-dev liblapack-dev libatlas-base-dev gfortran")
	try:
		os.system("sudo apt-get install ffmpeg python-cairocffi")
	except:
		pass # Debian won't bundle a couple packages.
	os.system("wget https://ufpr.dl.sourceforge.net/project/gridlab-d/gridlab-d/Candidate%20release/gridlabd-4.0.0-1.el6.x86_64.rpm")
	os.system("sudo alien gridlabd-4.0.0-1.el6.x86_64.rpm")
	workDir = os.getcwd()
	for file in os.listdir(workDir):
		if file.endswith(".deb"):
			debFile = file
	os.system("sudo dpkg -i " + debFile)
	os.system("sudo apt-get install -f")
	os.system("cd omf")
	os.system("pip install -r requirements.txt")
	os.system("python setup.py develop")
elif platform.system() == "Linux" and platform.linux_distribution()[0]=="CentOS Linux":
	os.system("sudo yum -y install wget git graphviz gcc xerces-c python-devel tkinter octave 'graphviz-devel.x86_64'")
	os.system("yum --enablerepo=extras install epel-release")
	os.system("sudo yum -y install mdbtools")
	os.system("sudo rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro")
	os.system("sudo rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-1.el7.nux.noarch.rpm")
	os.system("sudo yum -y install ffmpeg ffmpeg-devel -y")
	os.system("sudo yum -y install python-pip")
	os.system("wget --no-check-certificate https://ufpr.dl.sourceforge.net/project/gridlab-d/gridlab-d/Candidate%20release/gridlabd-4.0.0-1.el6.x86_64.rpm")
	os.system("rpm -Uvh gridlabd-3.2.0-1.x86_64.rpm")
	os.system("cd omf")
	os.system("pip install -r requirements.txt")
	os.system("pip install --ignore-installed six")
	os.system("python setup.py develop")
elif platform.system()=='Windows':
	# Need to manually download and install Chocolatey, python. 
	workDir = os.getcwd()
        version = sys.version.split('\n')[0] # Check for right Python version. This script shouldn't run at all if python isn't installed, right?
	if not version.startswith('2.'):
		os.system("choco install -y python2")

#	chocoString = @"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
 #   	os.system(chocoString)
	

    	os.system("choco install -y wget")
	os.system("choco install -y vcredist2008")
	os.system("choco install -y vcpython27")
	os.system("choco install -y ffmpeg")
	os.system("choco install -y graphviz")
	os.system("choco install -y pip")
    	os.system("choco install -y octave.portable")
        

	os.system("C:\Python27\python.exe -m pip install scipy")

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
	os.system('setx /M PATH "%PATH%;C:\Python27\Scripts"')
	os.system('setx /M PATH "%PATH%;C:\Program Files (x86)\Graphviz2.38\bin"')
	os.system("cd " + workDir)
	# Sometimes wget has a hard time downloading gridlabD
	if platform.architecture()[0] == '32bit':
		if 'gridlabd-3.2-win32.exe' not in os.listdir(workDir):
			os.system("wget --no-check-certificate https://ufpr.dl.sourceforge.net/project/gridlab-d/gridlab-d/Candidate%20release/gridlabd-4.0_RC1.exe")
			os.system("gridlabd-4.0_RC1.exe/silent")
		if 'pygraphviz-1.3.1-cp27-none-win32.whl' not in os.listdir(workDir):
			os.system("wget --no-check-certificate https://github.com/dpinney/omf/raw/master/omf/static/pygraphviz-1.3.1-cp27-none-win32.whl")
	elif platform.architecture()[1] == '64bit':
		# Note: has not been tested yet, only 32bit has.
		if 'gridlabd-3.2-x64.exe' not in os.listdir(workDir):
			os.system("wget --no-check-certificate https://ufpr.dl.sourceforge.net/project/gridlab-d/gridlab-d/Candidate%20release/gridlabd-4.0_RC1.exe")
			os.system("gridlabd-4.0_RC1.exe/silent")
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
        
elif platform.system()=="Darwin": # MacOS
	# Install homebrew
	os.system("/usr/bin/ruby -e '$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)'")
	os.system("brew install wget python ffmpeg git graphviz octave")
	os.system("brew link --overwrite python")
	os.system("wget -O gridlabd.dmg --no-check-certificate https://ufpr.dl.sourceforge.net/project/gridlab-d/gridlab-d/Candidate%20release/gridlabd_4.0.0.dmg")
	os.system("sudo hdiutil attach gridlabd.dmg")
	os.system("sudo installer -package /Volumes/GridLAB-D\ 4.0.0/gridlabd.mpkg -target /")
	os.system("sudo hdiutil detach /Volumes/GridLAB-D\ 4.0.0")
	os.system("cd omf")
	os.system("pip install -r requirements.txt")
	os.system("python setup.py develop")
else:
	print "Your operating system is not currently supported. Platform detected: " + str(platform.system()) + str(platform.linux_distribution())

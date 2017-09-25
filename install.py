import platform, os
# Use os.system('pass command as string')
if platform.system() == 'Linux':
	# if Ubuntu run these commands:
	if platform.linux_distribution()[0]=="Ubuntu":
		# git clone https://github.com/dpinney/omf.git
		os.system("sudo apt-get install python-pip git unixodbc-dev libfreetype6-dev \
		pkg-config python-dev python-numpy alien python-pygraphviz \
		python-pydot ffmpeg mdbtools python-cairocffi")
		os.system("wget https://sourceforge.net/projects/gridlab-d/files/gridlab-d/Last%20stable%20release/gridlabd-3.2.0-1.x86_64.rpm")
		os.system("sudo alien gridlabd-3.2.0-1.x86_64.rpm")
		os.system("sudo dpkg -i gridlabd-3.2.0-1.x86_64.deb")
		os.system("sudo apt-get install -f")
		os.system("cd omf")
		os.system("sudo python setup.py develop")
	# if CentOS 7 run these commands:
	elif platform.linux_distribution()[0]=="CentOS Linux":
		# git clone https://github.com/dpinney/omf.git
		os.system("sudo yum install wget git graphviz gcc xerces-c python-devel tkinter 'graphviz-devel.x86_64'")
		os.system("yum --enablerepo=extras install epel-release")
		os.system("sudo yum install mdbtools")
		os.system("sudo rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro")
		os.system("sudo rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-1.el7.nux.noarch.rpm")
		os.system("sudo yum install ffmpeg ffmpeg-devel -y")
		os.system("sudo yum install python-pip")
		os.system("wget https://sourceforge.net/projects/gridlab-d/files/gridlab-d/Last%20stable%20release/gridlabd-3.2.0-1.x86_64.rpm")
		os.system("rpm -Uvh gridlabd-3.2.0-1.x86_64.rpm")
		os.system("cd omf")
		os.system("pip install -r requirements.txt")
		os.system("pip install --ignore-installed six")
		os.system("python setup.py develop")
# if Windows run these commands:
elif platform.system()=='Windows':
	# git clone https://github.com/dpinney/omf.git
	workDir = os.getcwd()
	chocoString = '@"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString("https://chocolatey.org/install.ps1"))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"'
	os.system(chocoString)
	os.system("choco install -y git")
	os.system("choco install -y wget")
	os.system("choco install -y python2")
	os.system("choco install -y vcredist2008")
	os.system("choco install -y vcpython27")
	os.system("choco install -y ffmpeg")
	os.system("choco install -y graphviz")
	os.system("choco install -y pip")
	os.system("refreshenv")
	os.system("cd " + workDir)
	# wget pygraphviz 
	# pip install whl
	os.system("wget https://sourceforge.net/projects/gridlab-d/files/gridlab-d/Last%20stable%20release/gridlabd-3.2-win32.exe")
	os.system("gridlabd-3.2-win32.exe/silent")
	os.system("cd omf")
	os.system("pip install -r requirements.txt")
	os.system("pip install setuptools==33.1.1")
	os.system("python setup.py develop")
# if Mac run these commands:
elif platform.system()=="Darwin":
	print 'Mac'
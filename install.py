import platform, os, sys

def pipInstallInOrder(pipCommandString):
	with open("requirements.txt","r") as f:
		for line in f:
			os.system(pipCommandString + " install " + line)
	# Removes pip log files.
	os.system("rm \\=*")

# Note: all installations require git to clone the omf first.
if platform.system() == "Linux" and platform.linux_distribution()[0] in ["Ubuntu","debian"]:
	os.system("sudo apt-get -y install python-pip git unixodbc-dev libfreetype6-dev \
	pkg-config python-dev python-numpy alien graphviz python-pygraphviz libgraphviz-dev \
	python-pydot mdbtools python-tk octave libblas-dev liblapack-dev libatlas-base-dev gfortran wget")
	try:
		os.system("sudo apt-get -y install ffmpeg python-cairocffi")
	except:
		pass # Debian won't bundle a couple packages.
	os.system("wget https://ufpr.dl.sourceforge.net/project/gridlab-d/gridlab-d/Candidate%20release/gridlabd-4.0.0-1.el6.x86_64.rpm")
	os.system("sudo alien -i gridlabd-4.0.0-1.el6.x86_64.rpm")
	os.system("sudo apt-get install -f")
	os.system("cd omf")
	pipInstallInOrder("pip")
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
	pipInstallInOrder("pip")
	os.system("pip install --ignore-installed six")
	os.system("python setup.py develop")
elif platform.system()=='Windows':
	# Choco install.
	# chocoString = @"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
	# os.system(chocoString)
	# Check for right Python version.
	version = sys.version.split('\n')[0] 
	if not version.startswith('2.'):
		os.system("choco install -y python2")
	# Install choco packages.
	os.system("choco install -y wget")
	os.system("choco install -y vcredist2008")
	os.system("choco install -y ffmpeg")
	os.system("choco install -y graphviz")
	os.system("choco install -y pip")
	os.system("choco install -y octave.portable")
	#TODO: find way to install mdbtools.
	# HACK: timeout and refreshenv should get all the choco binaries on to the path.
	os.system("timeout 5")
	os.system("refreshenv")
	# Install GridLAB-D.
	os.system("wget --no-check-certificate https://ufpr.dl.sourceforge.net/project/gridlab-d/gridlab-d/Candidate%20release/gridlabd-4.0_RC1.exe")
	os.system("gridlabd-4.0_RC1.exe/silent")
	# Install pygraphviz.
	if platform.architecture()[0] == '32bit':
		os.system("C:\\Python27\\python.exe -m pip install omf\\static\\pygraphviz-1.3.1-cp27-none-win32.whl")
	elif platform.architecture()[0] == '64bit':
		os.system("C:\\Python27\\python.exe -m pip install omf\\static\\pygraphviz-1.3.1-cp27-none-win_amd64.whl")
	# Finish up installation with pip.
	os.system("cd omf")
	# HACK: more refreshes of the environment.
	os.system("timeout 5")
	os.system("refreshenv")
        os.system("C:\\Python27\\python.exe -m pip install scipy")
	os.system("C:\\Python27\\python.exe -m pip install setuptools>=33.1.1")
	pipInstallInOrder("C:\\Python27\\python.exe -m pip")
	os.system("C:\\Python27\\python.exe -m setup.py develop")
elif platform.system()=="Darwin": # MacOS
	# Install homebrew
	os.system('/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"')
	os.system("brew install wget python@2 ffmpeg git graphviz octave mdbtools")
	os.system("brew link --overwrite python")
	os.system("wget -O gridlabd.dmg --no-check-certificate https://ufpr.dl.sourceforge.net/project/gridlab-d/gridlab-d/Candidate%20release/gridlabd_4.0.0.dmg")
	os.system("sudo hdiutil attach gridlabd.dmg")
	os.system('sudo installer -package "/Volumes/GridLAB-D 4.0.0/gridlabd.mpkg" -target /')
	os.system('sudo hdiutil detach "/Volumes/GridLAB-D 4.0.0"')
	os.system("cd omf")
	pipInstallInOrder("pip2")
	os.system("python2 setup.py develop")
else:
	print "Your operating system is not currently supported. Platform detected: " + str(platform.system()) + str(platform.linux_distribution())

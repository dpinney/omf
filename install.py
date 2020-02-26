import platform, os, sys

def pipInstallInOrder(pipCommandString):
	''' This shouldn't be required, but pip doesn't resolve dependencies correctly unless we do this.'''
	with open("requirements.txt","r") as f:
		for line in f:
			os.system(pipCommandString + " install " + line)
	# Removes pip log files.
	os.system("rm \\=*")

if platform.system() == "Linux" and platform.linux_distribution()[0] in ["Ubuntu","debian"]:
	os.system("sudo apt-get -y update && sudo apt-get -y upgrade") # Make sure apt-get is updated to prevent any weird package installation issues
	os.system("sudo apt-get -y install language-pack-en") # Install English locale 
	os.system("sudo DEBIAN_FRONTEND=noninteractive apt-get -y install git python3-pip python3-dev python3-numpy python3-pygraphviz graphviz \
		unixodbc-dev libfreetype6-dev pkg-config alien libgraphviz-dev python3-pydot mdbtools python3-tk octave libblas-dev liblapack-dev \
		libatlas-base-dev gfortran wget splat")
	try:
		os.system("sudo apt-get -y install ffmpeg python3-cairocffi")
	except:
		pass # Debian won't bundle a couple packages.
	os.system("wget https://sourceforge.net/projects/gridlab-d/files/gridlab-d/Candidate%20release/gridlabd-4.0.0-1.el6.x86_64.rpm")
	os.system("sudo alien -i gridlabd-4.0.0-1.el6.x86_64.rpm")
	os.system("sudo apt-get install -f")
	os.system("cd omf")
	os.system("pip3 install --upgrade pip")
	pipInstallInOrder("pip3")
	os.system("python3 setup.py develop")
# TODO: Double check CentOS installation to support Python 3.7 or up
elif platform.system() == "Linux" and platform.linux_distribution()[0]=="CentOS Linux":
	# CentOS Docker image appears to come with en_US.UTF-8 locale built-in, but we might need to install that locale in the future. That currently is not done here.
	os.system("yum -y update") # Make sure yum is updated to prevent any weird package installation issues
	os.system("sudo yum -y install wget git graphviz gcc xerces-c python-devel tkinter octave 'graphviz-devel.x86_64'")
	os.system("yum --enablerepo=extras install epel-release")
	os.system("sudo yum -y install mdbtools")
	os.system("sudo rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro")
	os.system("sudo rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-1.el7.nux.noarch.rpm")
	os.system("sudo yum -y install ffmpeg ffmpeg-devel -y")
	os.system("sudo yum -y install python-pip")
	os.system("wget --no-check-certificate https://sourceforge.net/projects/gridlab-d/files/gridlab-d/Candidate%20release/gridlabd-4.0.0-1.el6.x86_64.rpm")
	os.system("rpm -Uvh gridlabd-4.0.0-1.el6.x86_64.rpm")
	os.system("cd omf")
	pipInstallInOrder("pip3")
	os.system("pip3 install --ignore-installed six")
	os.system("python3 setup.py develop")
elif platform.system()=='Windows':
	# Choco install.
	# chocoString = @"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
	# os.system(chocoString)
	# Check for right Python version.
	pybin = os.popen('where python').read()
	goodbin = 'C:\\Python36\\python.exe'
	if pybin != goodbin:
		print('Non-standard python install detected. We will attempt to continue with choco.')
		os.system("choco install -y python --version 3.6.8")
	# Hack to create a python3 binary on the path.
	os.system("copy C:\\Python36\\python.exe C:\\Python36\\python3.exe")
	# Update pip to remove warnings
	os.system("python3 -m pip install --upgrade pip")
	# Install choco packages.
	os.system("choco install -y wget")
	os.system("choco install -y vcredist-all")
	os.system("choco install -y ffmpeg")
	os.system("choco install -y graphviz")
	os.system("choco install -y pip")
	os.system("choco install -y octave.portable")
	#TODO: find way to install mdbtools.
	# HACK: timeout and refreshenv should get all the choco binaries on to the path.
	os.system("refreshenv")
	# Install GridLAB-D.
	os.system("wget --no-check-certificate https://sourceforge.net/projects/gridlab-d/files/gridlab-d/Candidate%20release/gridlabd-4.0_RC1.exe")
	os.system("gridlabd-4.0_RC1.exe/silent")
	os.system("refreshenv")
	#Install splat
	#os.system(wget https://www.qsl.net/kd2bd/Splat-1.3.0.zip)
	#os.system(Splat-1.3.0/Splat-1-3-1-SD-mx64.exe)
	# Install pygraphviz from wheel because it's finicky
	graphVizBinPath = "C:\\Program Files (x86)\\Graphviz2.38\\bin"
	os.system(f'setx path "%path%;{graphVizBinPath}"')
	os.system(f"set PATH=%PATH%;{graphVizBinPath}")
	os.system("python3.exe -m pip install omf\\static\\pygraphviz-1.5-cp36-cp36m-win_amd64.whl")
	# Finish up installation with pip.
	pipInstallInOrder("python3 -m pip")
	os.system("python3 -m setup.py develop")
elif platform.system()=="Darwin": # MacOS
	# Might need to install en_US.UTF-8 locale, like for Ubuntu? That currently is not done in this script. macOS might already come with this locale anyway.
	# Install homebrew
	brew_exit_code = os.system("brew --version")
	if brew_exit_code != 0:
		os.system('/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"')
	os.system("brew install wget python@3 ffmpeg git graphviz octave mdbtools")
	os.system("brew link --overwrite python")
	os.system("wget -O gridlabd.dmg --no-check-certificate https://sourceforge.net/projects/gridlab-d/files/gridlab-d/Candidate%20release/gridlabd_4.0.0.dmg")
	os.system("sudo hdiutil attach gridlabd.dmg")
	os.system('sudo installer -package "/Volumes/GridLAB-D 4.0.0/gridlabd.mpkg" -target /')
	os.system('sudo hdiutil detach "/Volumes/GridLAB-D 4.0.0"')
	#splat install
	#os.system("wget https://www.qsl.net/kd2bd/splat-1.4.2-osx.tgz")
	#os.system("sudo tar -xvzf splat-1.4.2-osx.tgz")
	#os.system("sudo exec splat-1.4.2/configure")
	os.system("cd omf")
	os.system('pip3 install --install-option="--include-path=/usr/local/include/" --install-option="--library-path=/usr/local/lib/" pygraphviz')
	os.system('pip3 install "ecos >= 2.0.7rc2"')
	pipInstallInOrder("pip3")
	os.system("python3 setup.py develop")
else:
	print("Your operating system is not currently supported. Platform detected: " + str(platform.system()) + str(platform.linux_distribution()))

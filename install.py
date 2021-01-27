import platform, os, sys

source_dir = os.path.dirname(__file__)

def pipInstallInOrder(pipCommandString):
	''' This shouldn't be required, but pip doesn't resolve dependencies correctly unless we do this.'''
	with open("requirements.txt","r") as f:
		for line in f:
			if not line.startswith('#'):
				os.system(pipCommandString + " install " + line)
	# Removes pip log files.
	os.system("rm \\=*")

if platform.system() == "Linux" and platform.linux_distribution()[0] in ["Ubuntu"]:
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
	os.system(f'octave-cli --no-gui -p "{source_dir}/omf/solvers/matpower7.0" --eval "install_matpower(1,1,1)"')
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
	os.system(f'octave-cli --no-gui -p "{source_dir}/omf/solvers/matpower7.0" --eval "install_matpower(1,1,1)"')
	os.system("cd omf")
	pipInstallInOrder("pip3")
	os.system("pip3 install --ignore-installed six")
	os.system("python3 setup.py develop")
elif platform.system()=='Windows':
	# Update pip to remove warnings
	os.system("python -m pip install --upgrade pip")
	# Install choco packages.
	os.system("choco install -y --no-progress wget")
	# os.system("choco install -y --no-progress vcredist-all")
	os.system("choco install -y --no-progress ffmpeg")
	os.system("choco install graphviz --no-progress --version=2.38.0.20171119")
	os.system("choco install -y --no-progress pip")
	os.system("choco install -y --no-progress octave.portable")
	# TODO: find way to install mdbtools.
	# Install GridLAB-D.
	os.system("wget --no-check-certificate https://sourceforge.net/projects/gridlab-d/files/gridlab-d/Candidate%20release/gridlabd-4.0_RC1.exe")
	os.system("gridlabd-4.0_RC1.exe/silent")
	#Install splat
	#os.system(wget http://www.ve3ncq.ca/software/SPLAT-1.3.1.zip)
	#os.system(unzip SPLAT-1.3.1.zip) #need to rename/copy these files.
	#os.system(f'octave-cli --no-gui -p "{source_dir}/omf/solvers/matpower7.0" --eval "install_matpower(1,1,1)"')
	# Install pygraphviz from wheel because it's finicky
	graphVizBinPath = 'C:\\Program Files (x86)\\Graphviz2.38\\bin'
	os.system(f'setx path "%path%;{graphVizBinPath}"')
	os.system(f"set PATH=%PATH%;{graphVizBinPath}")
	os.system("wget --no-check-certificate https://github.com/CristiFati/Prebuilt-Binaries/raw/master/PyGraphviz/v1.6/pygraphviz-1.6-cp37-cp37m-win_amd64.whl")
	os.system('python -m pip install pygraphviz-1.6-cp37-cp37m-win_amd64.whl')
	# os.system('python -m pip install omf\\static\\pygraphviz-1.5-cp36-cp36m-win_amd64.whl')
	# Finish up installation with pip.
	pipInstallInOrder("python -m pip")
	os.system("python setup.py develop")
	# os.system("refreshenv") # Refresh local environment variables via choco tool.
elif platform.system()=="Darwin": # MacOS
	# Install homebrew
	os.system("HOMEBREW_NO_AUTO_UPDATE=1 brew install wget ffmpeg git graphviz octave mdbtools") # Set no-update to keep homebrew from blowing away python3.
	os.system("wget -O gridlabd.dmg --no-check-certificate https://sourceforge.net/projects/gridlab-d/files/gridlab-d/Candidate%20release/gridlabd_4.0.0.dmg")
	os.system("sudo hdiutil attach gridlabd.dmg")
	os.system('sudo installer -package "/Volumes/GridLAB-D 4.0.0/gridlabd.mpkg" -target /')
	os.system('sudo hdiutil detach "/Volumes/GridLAB-D 4.0.0"')
	# splat install
	os.system("wget https://www.qsl.net/kd2bd/splat-1.4.2-osx.tgz")
	os.system("sudo tar -xvzf splat-1.4.2-osx.tgz")
	os.system('''
		cd splat-1.4.2;
		sed -i '' 's/ans=""/ans="2"/g' configure;
		sudo bash configure;
	''') # sed is to hack the build to work without user input.
	print('matpower dir', f"{source_dir}/omf/solvers/matpower7.0")
	os.system(f'octave-cli --no-gui -p "{source_dir}/omf/solvers/matpower7.0" --eval "install_matpower(1,1,1)"')
	# pip installs
	os.system("cd omf")
	os.system('pip3 install ecos')
	os.system('pip3 install pygraphviz --install-option="--include-path=/usr/local/include/graphviz" --install-option="--library-path=/usr/local/lib/graphviz/"')
	pipInstallInOrder("pip3")
	os.system("python3 setup.py develop")
else:
	print("Your operating system is not currently supported. Platform detected: " + str(platform.system()) + str(platform.linux_distribution()))

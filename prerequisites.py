import platform, os

if platform.system() == 'Linux':
    if platform.linux_distribution()[0]=='Ubuntu':
        os.system("sudo apt-get install python-pip git unixodbc-dev libfreetype6-dev \
                pkg-config python-dev python-numpy alien python-pygraphviz \
                python-pydot ffmpeg mdbtools python-cairocffi python-tk")
        os.system("wget https://sourceforge.net/projects/gridlab-d/files/gridlab-d/Last%20stable%20release/gridlabd-3.2.0-1.x86_64.rpm")
        os.system("sudo alien gridlabd-3.2.0-1.x86_64.rpm")
        os.system("sudo apt-get install libgraphviz-dev")
    elif platform.linux_distribution()[0]=="CentOS Linux":
                # git clone https://github.com/dpinney/omf.git
                os.system("sudo yum -y install wget git graphviz gcc xerces-c python-devel tkinter 'graphviz-devel.x86_64'")
                os.system("yum --enablerepo=extras install epel-release")
                os.system("sudo yum -y install mdbtools")
                os.system("sudo rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro")
                os.system("sudo rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-1.el7.nux.noarch.rpm")
                os.system("sudo yum -y install ffmpeg ffmpeg-devel -y")
                os.system("sudo yum -y install python-pip")
                os.system("wget --no-check-certificate https://sourceforge.net/projects/gridlab-d/files/gridlab-d/Last%20stable%20release/gridlabd-3.2.0-1.x86_64.rpm")
                os.system("rpm -Uvh gridlabd-3.2.0-1.x86_64.rpm")
elif platform.system()=='Windows':
        os.system("choco install -y git")
	os.system("choco install -y wget")
	os.system("choco install -y python2")
	os.system("choco install -y vcredist2008")
	os.system("choco install -y vcpython27")
	os.system("choco install -y ffmpeg")
	os.system("choco install -y graphviz")
	os.system("choco install -y pip")
elif platform.system()=="Darwin":
        print 'Mac'
        # Install homebrew
        os.system('/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"')
        os.system('brew install wget python ffmpeg git graphviz')
        os.system('brew link --overwrite python')
        # Works for gridlab version 3.2, will need to update when we use gridlabd v4
        os.system('wget -O gridlabd.dmg --no-check-certificate https://sourceforge.net/projects/gridlab-d/files/gridlab-d/Last%20stable%20release/gridlabd_3.2.0.dmg')
        os.system('sudo hdiutil attach gridlabd.dmg')
        os.system('sudo installer -package /Volumes/GridLAB-D\ 3.2.0/gridlabd.mpkg -target /')
        os.system('sudo hdiutil detach /Volumes/GridLAB-D\ 3.2.0')


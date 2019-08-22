#!/bin/bash

# This script installs the OMF on top of the existing GridState installation

# Install missing packages
apt-get -y update && apt-get install -y git python-pip wget sudo locales
# Generate a locale required by Cyme conversion in the OMF
sed -i 's/^# *\(en_US.UTF-8\)/\1/' /etc/locale.gen && locale-gen
# Get the repository
cd /home/jovyan
git clone https://github.com/dpinney/omf.git
cd /home/jovyan/omf
# Set the container environment such that Python commands point to the Python 2 installation
alias pip='sudo /usr/bin/pip2'
alias python='sudo /usr/bin/python2'
sudo mv /usr/local/bin/python /usr/local/bin/python.bkp
sudo mv /usr/local/bin/pip /usr/local/bin/pip.bkp
sudo ln -s /usr/bin/python /usr/local/bin/python
sudo ln -s /usr/bin/pip2 /usr/local/bin/pip
# Run the install script
sudo python install.py
# Restore the original GridState environment
sudo mv /usr/local/bin/python.bkp /usr/local/bin/python
sudo mv /usr/local/bin/pip.bkp /usr/local/bin/pip
unalias python
unalias pip
# Update this OMF install to the latest from the source tree.
if [ "$(id -u)" != "0" ]; then
	echo "This script must be run as root" 1>&2
	exit 1
else
	echo "** Stop the service."
	systemctl stop omf
	echo "** Backing up data folder."
	tar -czf ~/dataBackup.tgz /omf/omf/data
	cp /omf/omf/data/User/admin.json ~/admin.json
	cp /omf/omf/emailCredentials.key ~/emailCredentials.key
	echo "** Pulling the latest source from git."
	git reset --hard
	git pull
	echo "** Restoring our admin user and keys."
	cp ~/admin.json /omf/omf/data/User/admin.json
	cp ~/emailCredentials.key /omf/omf/emailCredentials.key	
	echo "** Setting permissions."
	chown -R root *
	chgrp -R root *
	echo "** Re-run install to handle any missing requirements."
	python /omf/install.py
	echo "** Restarting the service."
	systemctl start omf
fi
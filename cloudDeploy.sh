# Update this OMF install to the latest from the source tree.
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
echo "** Backing up data folder."
tar -czf ~/dataBackup.tgz /omf/omf/data
echo "** Pulling the latest source from git."
git reset --hard
git pull
echo "** Setting permissions."
chown -R omfwsgi *
chgrp -R omfwsgi *
echo "** Restarting Apache."
apachectl restart
# Update this version to the latest in the source tree.
if [ $# -eq 0 ]; then
	echo "Usage: cloudDeploy.sh <S3DatabaseKey>"
	exit
fi
echo "** Resetting to head and pulling the latest source from git."
git reset --hard
git pull
echo "** Updating database key."
sedHead='s/USER_PASS="YEAHRIGHT"/USER_PASS="'
sedTail='"/g'
sedArg=$sedHead$1$sedTail
sed -i $sedArg omf.py
echo "** Setting permissions."
chown -R omfwsgi *
chgrp -R omfwsgi *
echo "** Restarting Apache."
apachectl restart

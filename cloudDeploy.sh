# Update this version to the latest in the source tree.
if [ $# -eq 0 ]; then
	echo "Usage: cloudDeploy.sh <S3DatabaseKey>"
	exit
fi
echo "** Resetting to head and pulling the latest source from git."
git reset --hard
git pull
echo "** Updating database key."
echo -n "$1" > S3KEY.txt
echo "** Setting permissions."
chown -R omfwsgi *
chgrp -R omfwsgi *
echo "** Restarting Apache."
apachectl restart

# Update this version to the latest in the source tree.
if [ $# -eq 0 ]; then
	then
		echo "Usage: cloudDeploy.sh <S3DatabaseKey>"
fi
echo "** Resetting to head and pulling the latest source from git."
git reset --hard
git pull
echo "** Updating database key."
sed -i "s/USER_PASS='YEAHRIGHT'/USER_PASS='$1'/g" omf.py
echo "** Setting permissions."
chown -R wsgiuser *
chgrp -R wsgiuser *
echo "** Restarting Apache."
apachectl restart

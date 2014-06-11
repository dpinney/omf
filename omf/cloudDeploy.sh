# Update this OMF install to the latest from the source tree.
if [ $# -lt 2 ]; then
	echo "Usage: cloudDeploy.sh <S3DatabaseKey> <randomStringForSigningCookies>"
	exit
fi
echo "** Resetting to head and pulling the latest source from git."
git reset --hard
git pull
echo "** Updating database key."
echo -n "$1" > S3KEY.txt
echo -n "$2" > COOKIEKEY.txt
echo "** Setting permissions."
chown -R omfwsgi *
chgrp -R omfwsgi *
echo "** Restarting Apache."
apachectl restart

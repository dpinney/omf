# Update this OMF install to the latest from the source tree.
echo "** Resetting to head and pulling the latest source from git."
git reset --hard
git pull
echo "** Setting permissions."
chown -R omfwsgi *
chgrp -R omfwsgi *
echo "** Restarting Apache."
apachectl restart

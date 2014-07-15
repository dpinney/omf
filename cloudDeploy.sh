# Update this OMF install to the latest from the source tree.
echo "** Pulling the latest source from git."
git pull
echo "** Setting permissions."
chown -R omfwsgi *
chgrp -R omfwsgi *
echo "** Restarting Apache."
apachectl restart

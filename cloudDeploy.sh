# Update this version to the latest in the source tree.
echo "** Resetting to head and pulling the latest source from git."
git reset --hard
git pull
echo "** Setting permissions."
chown -R wsgiuser *
chgrp -R wsgiuser *
echo "** Restarting Apache."
apachectl restart

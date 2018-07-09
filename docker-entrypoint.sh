#!/bin/bash

echo "waiting on mysql"
while ! mysqladmin ping -h mysql --silent;do
	echo -n '.';
	sleep 1;
done
echo "ready"
sleep 1;

echo "strating"
python /flask/manager.py db init
python /flask/manager.py db migrate -m "initial migration"
python /flask/manager.py db upgrade
python /flask/manager.py deploy
/usr/bin/supervisord -c /etc/supervisord.conf

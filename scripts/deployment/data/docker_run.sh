#!/usr/bin/env bash

echo "Running docker container..."
cd /lerna

echo "- dependencies synchronization"
pip3 install --upgrade pip
pip3 install --upgrade -r requirements.txt
python3 manage.py sync --without-pip

echo "- log files creation"
mkdir -p /lerna/build/logs
touch /lerna/build/logs/nginx-errors.log
touch /lerna/build/logs/nginx-access.log

echo "- nginx launch"
nginx -t
nginx &

echo "- postfix launch"
service postfix start

echo "- launch gunicorn inside supervisor"
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf

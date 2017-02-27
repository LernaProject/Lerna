#!/usr/bin/env bash

echo "docker_run.sh started"
cd /lerna

echo "syncing all dependencies..."
pip3 install --upgrade pip
pip3 install --upgrade -r requirements.txt
python3 manage.py sync --without-pip

echo "creating log files..."
mkdir -p /lerna/build/logs
touch /lerna/build/logs/nginx-errors.log
touch /lerna/build/logs/nginx-access.log

echo "launching nginx..."
nginx -t
nginx &

echo "launching supervisor with gunicorn..."
/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf

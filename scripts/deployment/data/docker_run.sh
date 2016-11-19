#!/usr/bin/env bash

echo "docker_run.sh started"

echo "syncing all dependencies..."
cd /lerna
pip install -r requirements.txt --upgrade
python manage.py sync -p

echo "creating log files..."
# nginx launch
mkdir -p /lerna/build/logs
touch /lerna/build/logs/nginx-errors.log
touch /lerna/build/logs/nginx-access.log

echo "launching nginx..."
nginx -t
nginx &

echo "launching gunicorn..."
python manage.py runserver 0.0.0.0:3020

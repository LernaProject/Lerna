#!/usr/bin/env bash

echo "docker_run.sh started..."

echo "syncing all dependencies..."
cd /lerna
pip install -r requirements.txt --upgrade
python manage.py sync -p

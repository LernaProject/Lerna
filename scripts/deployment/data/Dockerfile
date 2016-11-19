FROM python:3.5
MAINTAINER Chernousov Ivan <krusnik.viers@gmail.com>

# Moving entry script to image and setting it as entry point
COPY docker_run.sh /
ENTRYPOINT ./docker_run.sh

# Preparing directory for lerna sources
RUN mkdir /lerna

# Updating available packages
RUN apt-get update

# Installing pip requirements
COPY requirements.txt.tmp /
RUN pip install -r requirements.txt.tmp --upgrade

# Setting up nginx
RUN apt-get install -y nginx
RUN echo "daemon off;" >> /etc/nginx/nginx.conf
RUN rm /etc/nginx/sites-enabled/*
RUN rm /etc/nginx/sites-available/*
COPY lerna.nginx /etc/nginx/sites-enabled

# Setting up gUnicorn
RUN pip install gunicorn

# Setting up supervisor
RUN apt-get install -y supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

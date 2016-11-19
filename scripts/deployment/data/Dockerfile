FROM python:3.5
MAINTAINER Chernousov Ivan <krusnik.viers@gmail.com>

# Moving entry script to image and setting it as entry point
COPY docker_run.sh /
ENTRYPOINT ./docker_run.sh

# Opening port for server
EXPOSE 3000

# Preparing directory for lerna sources
RUN mkdir /lerna

# Installing pip requirements
COPY requirements.txt.tmp /
RUN pip install -r requirements.txt.tmp --upgrade

# Setting up nginx
RUN apt-get update && apt-get install -y nginx
RUN echo "daemon off;" >> /etc/nginx/nginx.conf
RUN rm /etc/nginx/sites-enabled/*
RUN rm /etc/nginx/sites-available/*
COPY nginx.conf /etc/nginx/sites-enabled

FROM python:3.5
MAINTAINER Chernousov Ivan <krusnik.viers@gmail.com>

# Moving entry script to image and setting it as entry point
COPY docker_run.sh /
ENTRYPOINT ./docker_run.sh

# Opening 80 port
EXPOSE 80

# Prepating directory for lerna sources
RUN mkdir /lerna

FROM python:3-buster
RUN apt-get update
RUN apt-get install -y unzip wget mosquitto-clients
RUN pip install --upgrade pip
RUN pip install arena-py

WORKDIR /usr/src/app

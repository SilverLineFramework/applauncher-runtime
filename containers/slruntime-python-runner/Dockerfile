FROM python:3-buster
RUN apt-get update
RUN apt-get install -y unzip wget mosquitto-clients
RUN pip install --upgrade pip
WORKDIR /tmp
COPY requirements.txt .
RUN pip install -r requirements.txt 

WORKDIR /usr/src/app
COPY entrypoint.sh /

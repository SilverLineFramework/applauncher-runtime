FROM python:3-buster
RUN apt-get update
RUN pip install --upgrade pip
RUN pip install certifi
WORKDIR /tmp
COPY requirements.txt .
RUN pip install -r requirements.txt 

WORKDIR /usr/src/app
COPY entrypoint.sh /

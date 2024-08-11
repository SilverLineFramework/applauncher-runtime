FROM python:3.12.5
RUN apt-get update
RUN apt-get install -y unzip wget mosquitto-clients
RUN pip install --upgrade pip
WORKDIR /tmp
# intall arena-py from repo head 
RUN git clone https://github.com/arenaxr/arena-py.git
WORKDIR /tmp/arena-py
RUN `which python3` -m pip install -e .

WORKDIR /usr/src/app
COPY entrypoint.sh /

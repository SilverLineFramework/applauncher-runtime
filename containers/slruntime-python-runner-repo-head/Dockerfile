FROM python:3.12.5
RUN pip install --upgrade pip
WORKDIR /tmp
COPY requirements.txt .
RUN pip install -r requirements.txt 

# intall arena-py from commit pointed by VERSION
RUN git clone https://github.com/arenaxr/arena-py.git
WORKDIR /tmp/arena-py
COPY VERSION .
RUN git checkout $(cat VERSION)
RUN `which python3` -m pip install -e .

WORKDIR /usr/src/app
COPY entrypoint.sh /

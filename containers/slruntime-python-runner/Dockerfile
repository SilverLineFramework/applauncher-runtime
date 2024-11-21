FROM python:3.12.5
RUN pip install --upgrade pip
RUN pip install certifi
WORKDIR /tmp
COPY requirements.txt .
RUN pip install -r requirements.txt 
COPY VERSION .
RUN pip install --force-reinstall -v "arena-py==$(cat VERSION)"

WORKDIR /usr/src/app
COPY entrypoint.sh /

FROM ubuntu:20.04

RUN apt update
ARG DEBIAN_FRONTEND=noninteractive
RUN apt -y install wget git software-properties-common build-essential
RUN apt -y install -y python3 python3-pip

WORKDIR /tmp/
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt -y install ./google-chrome-stable_current_amd64.deb


RUN mkdir -p /opt/code/photo-downloader/downloads
WORKDIR /opt/code/photo-downloader

COPY . .
RUN pip3 install -r requirements.txt

CMD "flask run"
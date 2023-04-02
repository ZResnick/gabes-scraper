#!/bin/bash

flask_app_pid=$(ps aux | grep flask | grep photo | tr -s ' ' | cut -d ' ' -f 2)
if [[ -n flask_app_pid ]]; then
	kill -9 $flask_app_pid;
fi;

cd /photo-downloader-master/
python3 -m venv venv
. venv/bin/activate
source venv/bin/activate
pip3 install -r requirements.txt
flask run --debug -p5111 &
cd ../photo-downloader-frontend-master/
npm install
npm start
#!/bin/bash

flask_app_pid=$(ps aux | grep flask | grep photo | tr -s ' ' | cut -d ' ' -f 2)
if [[ -n flask_app_pid ]]; then
	kill -9 $flask_app_pid;
fi;


cd ~/Desktop/SmugMugScraper/photo-downloader-master/
python3 -m venv venv
. venv/bin/activate
source venv/bin/activate
pip3 install -r requirements.txt
flask run --debug -p5111 &
cd ~/Desktop/SmugMugScraper/photo-downloader-frontend-master/
nvm install 14.15.5
nvm use 14.15.5 
npm install
npm start
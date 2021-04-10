#!/bin/bash

clear ;
echo "Starting STOP THE BUS server...";
source ~/apps/stb/stb_venv/bin/activate ;
exec gunicorn -k eventlet -w 1 --bind 0.0.0.0:7777 server:app

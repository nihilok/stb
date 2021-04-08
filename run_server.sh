#!/bin/bash

clear ;
echo "Starting STOP THE BUS server..."
source /mnt/f/Coding/stb/wsl/venv/bin/activate ;
gunicorn -k eventlet -w 1 --bind 0.0.0.0:7777 stb_server:app

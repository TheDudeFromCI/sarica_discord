#!/bin/bash

dev_flag=''

while getopts 'd' flag; do
  case "${flag}" in
    d) dev_flag='true' ;;
    *) echo "Usage: $0 [-d]" >&2; exit 1 ;;
  esac
done

if [ "$dev_flag" = 'true' ]; then
  echo "Running Sarica in development mode"
else
  echo "Running Sarica in production mode"
  git pull
fi

source .venv/bin/activate
pip install -r requirements.txt
python3 main.py

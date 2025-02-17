#!/bin/bash

dev_flag=''

while getopts 'd' flag; do
  case "${flag}" in
    d) dev_flag='true' ;;
    *) echo "Usage: $0 [-d]" >&2; exit 1 ;;
  esac
done

SARICA_VERSION_HASH=$(git rev-parse --short HEAD)
export SARICA_VERSION_HASH

if [ "$dev_flag" = 'true' ]; then
  echo "Running Sarica in development mode"
  python3 main.py
else
  echo "Running Sarica in production mode"
  git pull

  source .venv/bin/activate
  pip install -r requirements.txt
  python3 main.py > latest.log 2>&1 &
fi

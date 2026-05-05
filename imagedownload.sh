#!/usr/bin/env fish
echo "Starting Environment"
#python3.11 -m venv ./.01
source .01/bin//activate.fish
python3 apitest.py

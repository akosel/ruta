#!/bin/bash

sudo apt update

# most commands run with make
sudo apt install make

# new gpio library that works with newer linux kernels
# excellent post on this here: https://waldorf.waveform.org.uk/2021/the-pins-they-are-a-changin.html
sudo apt install python3-lgpio

# this might be bad form, but make sure python is a valid command
sudo apt install python-is-python3

# install pip
sudo apt install python3-pip

sudo apt install nginx

# install poetry for python dependency management
# see https://python-poetry.org/docs/ for details
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -

make install
make migrate
make createsuperuser

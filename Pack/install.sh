#!/bin/bash

WORKSPACE=~/.qviz/
ENVSPACE=/usr/local/qviz_env
sudo rm -r $ENVSPACE
sudo ln -s $PWD $WORKSPACE
sudo ln -s $PWD/qviz_env $ENVSPACE


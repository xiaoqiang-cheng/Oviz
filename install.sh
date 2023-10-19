#!/bin/bash

WORKSPACE=~/.oviz
ENVSPACE=/usr/local/oviz_env
sudo rm $WORKSPACE
#sudo rm -r $ENVSPACE
sudo ln -s $PWD $WORKSPACE
# sudo ln -s $PWD/oviz_env $ENVSPACE
sudo cp ./Pack/oviz /usr/bin/
echo "install done!"

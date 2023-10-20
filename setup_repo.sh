# !bin\bash

# Author: Max Bergmann
# Description: This script will setup your Repository by initializing submodules and switching to right branches


# setup submodules
git submodule --init
git submodule --update

cd mini-internet
git checkout mini-ipd

cd ../ipd-implementation
git checkout mini-ipd
# !bin\bash

# Author: Max Bergmann
# Description: This script will setup your Repository by initializing submodules and switching to right branches


# check if Miniconda already exists and path to it is given
if [ -z "$1" ];
then
    # install Miniconda3
    mkdir -p miniconda3
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda3/miniconda.sh
    bash miniconda3/miniconda.sh -b -u -p miniconda3
    rm -rf miniconda3/miniconda.sh

    # activate Miniconda3
    miniconda3/bin/conda init bash
    miniconda3/bin/conda init zsh

    start_dir=$(pwd)
    miniconda="${start_dir}/miniconda3"
    # setup Conda environment
    conda config --add channels conda-forge
    conda create --name mini-ipd --file requirements.txt --yes
else
    miniconda=$1
    installed=$2

    if [ $installed -eq 0 ];
    then
        # setup Conda environment
        conda config --add channels conda-forge
        conda create --name mini-ipd --file requirements.txt --yes
    fi
fi

# enable access to python environment for hosts
echo COPY MINICONDA ENV TO MOUNTED FOLDER OF HOSTS
sudo cp -r ${miniconda} shared_directories/host_files

# setup submodules
git submodule init
git submodule update

cd mini-internet
git checkout mini-ipd

cd ../ipd-implementation
git checkout mini-ipd

echo START EXAMPLE MINI-IPD
cd ..
sudo bash ./start_mini_ipd_example.sh ${miniconda}

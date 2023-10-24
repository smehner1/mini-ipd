# !bin\bash

# Author: Max Bergmann
# Description: TBD

miniconda=$1
PYTHON=${miniconda}/envs/mini-ipd/bin/python3

start=$(pwd)

# generate configurations for 5 ASes
cd scalability
$PYTHON create_mini_internet_configs.py 5


# Start Mini-Internet
cd ../mini-internet/platform

# build Docker Container for router, host and IXP
docker build --tag=thomahol/d_router docker_images/router/
docker build --tag=thomahol/d_ixp docker_images/ixp/
docker build --tag=thomahol/d_host docker_images/host/

bash ./startup.sh
bash ./startup_additional_scripts.sh kill
bash ./startup_additional_scripts.sh


# configure Mini-Internet for IPD usage
cd ../../configurator
$PYTHON configure.py


# Start a 2-hour Traffic Generation Task
cd ../traffic_generator
bash ./generate_day_traffic.sh ${miniconda}

cd $start
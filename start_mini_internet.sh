# !bin\bash

# Author: Max Bergmann
# Description: starts the Mini-Internet with given configurations and prepares it for IPD usage

miniconda=$1
PYTHON=${miniconda}/envs/mini-ipd/bin/python3

start=$(pwd)

# Start Mini-Internet
cd ../mini-internet/platform

# build Docker Container for router, host and IXP
docker build --tag=thomahol/d_router docker_images/router/
docker build --tag=thomahol/d_ixp docker_images/ixp/
docker build --tag=thomahol/d_host docker_images/host/

docker build --tag=d_ssh docker_images/ssh/
docker build --tag=d_measurement docker_images/measurement/
docker build --tag=d_dns docker_images/dns/
docker build --tag=d_switch docker_images/switch/
docker build --tag=d_matrix docker_images/matrix/
docker build --tag=d_vpn docker_images/vpn/
docker build --tag=d_vlc docker_images/vlc/
docker build --tag=d_hostm docker_images/hostm/

bash ./startup.sh
bash ./startup_additional_scripts.sh kill
bash ./startup_additional_scripts.sh ${miniconda}


# configure Mini-Internet for IPD usage
cd ../../configurator
$PYTHON configure.py

cd $start

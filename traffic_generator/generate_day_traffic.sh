#!/bin/bash

# Author: Max Bergmann


PYTHON="/home/max/WORK/masterthesis/miniconda3/envs/mini/bin/python3"

# $PYTHON /home/max/WORK/masterthesis/mini_internet_tools/traffic_generator/traffic_controller.py --start -w 3600 -f 5000 -g

$PYTHON /home/max/WORK/masterthesis/mini_internet_tools/netflow_collector/netflow_collector.py | $PYTHON /home/max/WORK/masterthesis/mini_internet_tools/traffic_generator/traffic_controller.py --start -w 3600 -f 5000
# $PYTHON /home/max/WORK/masterthesis/mini_internet_tools/traffic_generator/traffic_controller.py --start -w 900 -f 5000

$PYTHON /home/max/WORK/ipd-implementation/tools/connect_netflow.py

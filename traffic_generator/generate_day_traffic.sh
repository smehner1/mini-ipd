#!/bin/bash

# Author: Max Bergmann


CONDA=$1
PYTHON=${CONDA}/envs/mini-ipd/bin/python3


screen -d -m -S netflow_collector bash -c "$PYTHON ../netflow_collector/netflow_collector.py -conda $CONDA -v"
$PYTHON traffic_controller.py --start -w 60 -f 5000 --killcollector --conda $CONDA
# $PYTHON ../ipd-implementation/tools/connect_netflow.py

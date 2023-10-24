#!/bin/bash

# Author: Max Bergmann


CONDA=$1
PYTHON=${CONDA}/envs/mini-ipd/bin/python3


$PYTHON ../netflow_collector/netflow_collector.py | $PYTHON traffic_controller.py --start -w 300 -f 5000 -g
$PYTHON ../ipd-implementation/tools/connect_netflow.py

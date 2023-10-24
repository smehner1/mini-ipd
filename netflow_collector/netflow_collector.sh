#!/bin/bash

# Author: Max Bergmann


netflow_path=$1
date=$2
dst_path=$3

PYTHON="/home/max/WORK/masterthesis/miniconda3/envs/mini/bin/python3"

chmod ugo+rw -R ${netflow_path}

$PYTHON /home/max/WORK/masterthesis/mini_internet_tools/netflow_collector/preprocess_netflow.py -nf ${netflow_path}${date}/ -outname ${netflow_path}/preprocessed_${date}

rm -rf ${dst_path}

zcat ${netflow_path}/preprocessed_${date}.csv.gz

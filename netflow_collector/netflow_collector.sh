#!/bin/bash

# Author: Max Bergmann


netflow_path=$1
date=$2
dst_path=$3
conda_dir=$4
collector_dir=$5

PYTHON=$conda_dir/envs/mini/bin/python3

chmod ugo+rw -R ${netflow_path}

$PYTHON ${collector_dir}/preprocess_netflow.py -nf ${netflow_path}${date}/ -outname ${netflow_path}/preprocessed_${date}

rm -rf ${dst_path}

zcat ${netflow_path}/preprocessed_${date}.csv.gz

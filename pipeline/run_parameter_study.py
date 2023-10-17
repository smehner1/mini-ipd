#!/usr/bin/python3

import os
import gzip
import glob
import time
import subprocess
import pandas as pd

from typing import Tuple
from datetime import datetime

from helper import get_parametrizations, Spinner


__author__ = 'Max Bergmann'


# RUN IPD WITH ALL PARAMETERIZATIONS
result_dir: str = '/home/max/WORK/ipd-implementation/algo/results/noise_experiment_2'
ressource_dir: str = '/home/max/WORK/ipd-implementation/algo/resource_log/noise_experiment_2/'
data_dir: str = '/home/max/WORK/masterthesis/pipeline/data/ranges/offload2/'
range_dir: str = '/home/max/WORK/masterthesis/pipeline/data/ranges/'


def connect_rangefiles(path: str, paras: Tuple, test: str) -> None:
    '''
    connects all range files in given directory and saves them into data/ranges/. This also includes postprocessing for
    creating needed format with separate ip and mask etc.

    Arguments
    ---------
    path (str): path to directory of created ranges files of IPD
    paras (tuple): tuple that includes all parameters to connect range files for
    test (str): identification of project running (e.g., parameter_study)
    '''
    if os.path.isdir(path):
        # connect range files without processing
        result_file = open(f'{range_dir}/{test}/{path.split("/")[-2]}.range', 'w')
        files: list = glob.glob(path + '/*')
        for file in files:
            f = gzip.open(file, 'rt')
            for line in f:
                result_file.write(line)
            f.close()
        result_file.close()
        # process connected range files
        try:
            ranges_df: pd.DataFrame = pd.read_csv(
                f'{range_dir}/{test}/{path.split("/")[-2]}.range',
                sep='\t',
                header=None
            )
            ranges_df.columns = [
                't',
                'ip_version',
                'range',
                'confidence',
                'counter_samples/counter_samples_needed',
                'ip_mask',
                'ingress_router',
            ]

            paras_cols: list = [
                'parameter_q',
                'parameter_c4',
                'parameter_c6',
                'parameter_cidr_max4',
                'parameter_cidr_max6',
                'parameter_t',
                'parameter_e',
                'parameter_decay',
            ]
            for i in range(len(paras_cols)):
                ranges_df[paras_cols[i]] = len(ranges_df) * [paras[i]]

            # add new columns
            ranges_df['parameter_study_name'] = len(ranges_df) * [path.split("/")[-2]]
            ranges_df['prefix_asn'] = ranges_df['ingress_router']
            ranges_df['netid_string'] = ranges_df['ip_mask']
            ranges_df['mask'] = ranges_df['ip_mask']
            ranges_df['counter_samples'] = ranges_df['counter_samples/counter_samples_needed']
            ranges_df['counter_samples_needed'] = ranges_df['counter_samples/counter_samples_needed']
            ranges_df['pni'] = len(ranges_df) * [0]

            # process new columns to get wanted values
            ranges_df['prefix_asn'] = ranges_df['prefix_asn'].apply(lambda x: x.split('_')[1])
            ranges_df['netid_string'] = ranges_df['netid_string'].apply(lambda x: x.split('/')[0])
            ranges_df['mask'] = ranges_df['mask'].apply(lambda x: x.split('/')[1])
            ranges_df['counter_samples'] = ranges_df['counter_samples'].apply(lambda x: int(x.split('/')[0]))
            ranges_df['counter_samples_needed'] = ranges_df['counter_samples_needed'].apply(
                lambda x: int(x.split('/')[1]))

            ressources_df: pd.DataFrame = pd.read_csv(f'{ressource_dir}/{path.split("/")[-2]}.log')
            # print(path.split("/")[-2])
            ressource_cols = ressources_df.columns.to_list()
            ressource_cols[0] = 't'
            ressources_df.columns = ressource_cols
            add_frame: pd.DataFrame = pd.DataFrame(
                columns=['ipd_ranges_count', 'ipd_cpu_runtime', 'iteration_cpu_runtime', 'ram_usage'])
            for _, row in ranges_df.iterrows():
                res = ressources_df.query(f't == {row["t"]}')
                add_frame = pd.concat([
                    add_frame,
                    res[['ipd_ranges_count', 'ipd_cpu_runtime', 'iteration_cpu_runtime', 'ram_usage']]
                ])

            for c in add_frame.columns:
                ranges_df[c] = add_frame[c].to_list()

            # print(f'save to {range_dir}/{test}/range_{path.split("/")[-2]}.csv.gz')

            ranges_df.drop(['range', 'counter_samples/counter_samples_needed', 'ip_mask'], axis=1, inplace=True)
            ranges_df.sort_values('t', inplace=True)
            print(ranges_df.shape)
            ranges_df.to_csv(
                f'{range_dir}/{test}/range_{path.split("/")[-2]}.csv.gz',
                compression='gzip',
                header=None,
                sep=',',
                index=False)
            os.popen(f'rm {range_dir}/{test}/{path.split("/")[-2]}.range')
        except pd.errors.EmptyDataError:
            pd.DataFrame().to_csv(
                f'{range_dir}/{test}/range_{path.split("/")[-2]}.csv.gz',
                compression='gzip',
                header=None,
                sep=',',
                index=False)
            os.popen(f'rm {range_dir}/{test}/{path.split("/")[-2]}.range')


def check_finished_ipds(parametrizations: pd.DataFrame, file: str) -> pd.DataFrame:
    '''
    will check if the IPD wrapper with the given parametrizations is still running. If not running it connects the
    created range files

    Arguments
    ---------
    parametrization (DataFrame): Frame that includes all still running parametrizations
    file (str): path to netflow file

    Returns
    -------
    parametrization (DataFrame): Frame that includes all still running parametrizations
    '''
    for _, row in parametrizations.iterrows():
        # read the processes running with given parametrization and check if file empty to check if process finished
        os.system((f'ps -ef | grep "start_algo_pipe.sh {row["q"]} {row["c4"]} {row["c6"]} {row["cidr4"]} {row["cidr6"]}'
                   f' {file}" | grep -v grep > tmp.txt'))
        if os.stat('tmp.txt').st_size == 0:  # process of this parametrization finished
            path: str = (f"{result_dir}/q{row['q']}_c{row['c4']}-{row['c6']}_cidr_max{row['cidr4']}-{row['cidr6']}_t"
                         f"{row['t']}_e{row['e']}_decay{row['decay']}/")
            # connect range_files
            connect_rangefiles(
                path,
                (row['q'], row['c4'], row['c6'], row['cidr4'], row['cidr6'], row['e'], row['t'], row['decay']),
                file.split('/')[-1].split('.')[0]
            )
            # remove finished parametrizations from frame to not check it again
            parametrizations: pd.DataFrame = parametrizations.drop(
                parametrizations.query((f'q == {row["q"]} and c4 == {row["c4"]} and c6 == {row["c6"]} and cidr4 == '
                                        f'{row["cidr4"]} and cidr6 == {row["cidr6"]} and t == {row["t"]} and e == '
                                        f'{row["e"]} and decay == "{row["decay"]}"')).index,
                axis=0,
            )
            # remove range files
            os.system(f'rm -rf {path}')
            print()
            print(f'----- IPD FOR {path.split("/")[-2]} FINISHED! CONNECT RANGE FILES -----')
            print(f'----- {len(parametrizations)} IPDs STILL RUNNING -----')
            print()

    os.system('rm tmp.txt')  # remove the temporary file

    return parametrizations


def run_ipd(parametrizations: pd.DataFrame, q: float, file: str) -> None:
    '''
    starts the IPD for all parametrizations with given q and connect the range files after finishing the process

    Arguments
    ---------
    parametrizations (DataFrame): Frame with all possible parametrizations
    q (float): the q value to execute the IPD with
    file (str): file to netflow data
    '''
    # parametrizations = parametrizations.iloc[[0, 1, 2]]
    start: datetime = datetime.now()
    parametrizations = parametrizations.query(f'q=={q}')
    print(len(parametrizations))
    print('----- REMOVE OLD RANGE FILES IF NOT DELETED AND START IPDs -----')
    counter: int = 0
    # ----- EXECUTE IPD -----
    for index, row in parametrizations.iterrows():
        path: str = (f"{result_dir}/q{row['q']}_c{row['c4']}-{row['c6']}_cidr_max{row['cidr4']}-{row['cidr6']}_t"
                     f"{row['t']}_e{row['e']}_decay{row['decay']}/")
        # rm possible old directory with old result/range files
        print('----- REMOVE OLD RANGE FILES IF NOT DELETED -----')
        os.system(f'rm -rf {path}')
        # execute IPD
        print('----- EXECUTE IPD WITH ... -----')
        subprocess.Popen(
            (f"bash /home/max/WORK/ipd-implementation/start_algo_pipe.sh {row['q']} {row['c4']} "
             f"{row['c6']} {row['cidr4']} {row['cidr6']} {file}"),
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT
        )
        counter += 1
    print(f'----- STARTED {counter} IPD RUNS -----')
    print()

    with Spinner():
        time.sleep(30)
        while len(parametrizations) > 0:
            parametrizations = check_finished_ipds(parametrizations, file)
            time.sleep(1)

    end: datetime = datetime.now()
    print(f'FINISHED {counter} IPD RUNS after {end-start}')


if __name__ == '__main__':
    tests = [
        '/home/max/WORK/ipd-implementation/netflow/netflow_25k_overflow.csv.gz',

        '/home/max/WORK/ipd-implementation/netflow/netflow_25k_0_noise.csv.gz',
        '/home/max/WORK/ipd-implementation/netflow/netflow_25k_10_noise.csv.gz',
        '/home/max/WORK/ipd-implementation/netflow/netflow_25k_20_noise.csv.gz',
        '/home/max/WORK/ipd-implementation/netflow/netflow_25k_30_noise.csv.gz',
        '/home/max/WORK/ipd-implementation/netflow/netflow_25k_40_noise.csv.gz',
        '/home/max/WORK/ipd-implementation/netflow/netflow_25k_50_noise.csv.gz',
        '/home/max/WORK/ipd-implementation/netflow/netflow_25k_60_noise.csv.gz',
        '/home/max/WORK/ipd-implementation/netflow/netflow_25k_70_noise.csv.gz',
        '/home/max/WORK/ipd-implementation/netflow/netflow_25k_80_noise.csv.gz',
        '/home/max/WORK/ipd-implementation/netflow/netflow_25k_90_noise.csv.gz',
        '/home/max/WORK/ipd-implementation/netflow/netflow_25k_100_noise.csv.gz',
    ]
    parametrizations: pd.DataFrame = get_parametrizations()

    for test in tests:
        t = test.split('/')[-1].split('.')[0]

        # create range folder if not exists
        if not os.path.exists(f'{range_dir}/{t}'):
            os.mkdir(f'{range_dir}/{t}')

        for q in parametrizations['q'].unique():
            run_ipd(parametrizations, q, test)

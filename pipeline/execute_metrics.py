#!/usr/bin/python3

import os
import time
import pandas as pd

from helper import Spinner
from helper import CLIENT, NUM_KNOWN_AS
from helper import get_query_w_columns, get_parametrizations

from stability import get_data, connect
from granularity import get_granularity


__author__ = 'Max Bergmann'


parametrizations: pd.DataFrame = get_parametrizations()
study: str = 'mini_internet'


def get_conv_as(params: str) -> pd.DataFrame:
    '''
    calculate the AS coverage for parametrization per timestamp

    Arguments
    ---------
    params (str): parametrization as string to calculate coverage

    Returns
    -------
    frame (DataFrame): dataframe including the timesteps with corresponding coverage
    '''
    query, columns = get_query_w_columns('dist_num_as_ts', params)

    # get data
    result: list = CLIENT.execute(query)
    num_as: pd.DataFrame = pd.DataFrame(data=result, columns=columns)

    # normalize to number of known ASs
    data: pd.Series = num_as['num_as'].apply(lambda count: count/NUM_KNOWN_AS*100)
    timesteps: list = num_as['timestep'].to_list()

    frame: pd.DataFrame = pd.DataFrame({
        'conv_as': data.to_list()
    }, index=timesteps)

    return frame


def get_conv_ips(params: str) -> pd.DataFrame:
    '''
    calculate the IP address space coverage for parametrization per timestamp

    Arguments
    ---------
    params (str): parametrization as string to calculate coverage

    Returns
    -------
    frame (DataFrame): dataframe including the timesteps with corresponding coverage
    '''
    query, columns = get_query_w_columns('num_ips_share', params)
    result: list = CLIENT.execute(query)

    num_prefix: pd.DataFrame = pd.DataFrame(data=result, columns=['t', 'num_ips_top_as', 'share'])

    frame: pd.DataFrame = pd.DataFrame({
        'conv_ips': num_prefix['share'].to_list()
    }, index=num_prefix['t'].to_list())

    return frame


def get_granu(params: str) -> pd.DataFrame:
    '''
    calculate the granularity for parametrization per timestamp

    Arguments
    ---------
    params (str): parametrization as string to calculate granularity

    Returns
    -------
    frame (DataFrame): dataframe including the timesteps with corresponding granularity
    '''
    granularity: pd.DataFrame = get_granularity(params)

    frame: pd.DataFrame = pd.DataFrame({
        'granularity': granularity['granularity'].to_list()
    }, index=granularity['timestep'].to_list())

    return frame


def get_ressources(params: str) -> pd.DataFrame:
    '''
    get resource metrics for parametrization per timestamp

    Arguments
    ---------
    params (str): parametrization as string to get ressources for

    Returns
    -------
    frame (DataFrame): dataframe including the timesteps with corresponding ressources
    '''
    query, columns = get_query_w_columns('ressources', params)

    data: list = CLIENT.execute(query)
    ressources_df: pd.DataFrame = pd.DataFrame(data, columns=columns)
    ressources_df.index = ressources_df['timestep']
    ressources_df.drop('timestep', inplace=True, axis=1)

    return ressources_df


def insert_into_clickhouse() -> None:
    '''insert ranges of all parametrizations into clickhouse db'''
    print('----- INSERT DATA INTO CLICKHOUSE -----')
    with Spinner():
        for _, row in parametrizations.iterrows():
            para: str = (f"q{row['q']}_c{row['c4']}-{row['c6']}_cidr_max{row['cidr4']}-{row['cidr6']}_t{row['t']}"
                         f"_e{row['e']}_decay{row['decay']}")
            # insert file into clickhouse
            os.system((f'bash insert.sh {para} {row["q"]} {row["c4"]} {row["c6"]} {row["cidr4"]} '
                       f'{row["cidr6"]} {row["t"]} {row["e"]} {row["decay"]}'))
            time.sleep(0.5)
            # compress the file
            # os.popen(f'gzip -f {BITHOUSE}/ranges/range_{para}.csv')


def calc_metrics() -> None:
    '''calculate the metrics for all parametrizations'''
    metrics: pd.DataFrame = pd.DataFrame(
            columns=[
                'timestep',
                'conv_as',
                'conv_ips',
                'granularity',
                'ipd_ranges_count',
                'ipd_cpu_runtime',
                'iteration_cpu_runtime',
                'ram_usage',
                'parameter_q',
                'parameter_c4',
                'parameter_c6',
                'parameter_cidr_max4',
                'parameter_cidr_max6',
                'parameter_t',
                'parameter_e',
                'parameter_decay',
                'parameter_study_name',
                'parameter_study_type',
            ]
        )
    print('----- CALCULATE METRICS -----')
    with Spinner():
        for _, row in parametrizations.iterrows():
            para: str = (f"q{row['q']}_c{row['c4']}-{row['c6']}_cidr_max{row['cidr4']}-{row['cidr6']}_t{row['t']}"
                         f"_e{row['e']}_decay{row['decay']}")

            as_frame: pd.DataFrame = get_conv_as(para)
            ips_frame: pd.DataFrame = get_conv_ips(para)
            granu_frame: pd.DataFrame = get_granu(para)
            ressources_frame: pd.DataFrame = get_ressources(para)

            param_metrics: pd.DataFrame = pd.concat([as_frame, ips_frame, granu_frame, ressources_frame], axis=1)
            param_metrics['timestep'] = param_metrics.index.to_list()
            param_metrics['parameter_q'] = len(param_metrics) * [row['q']]
            param_metrics['parameter_c4'] = len(param_metrics) * [row['c4']]
            param_metrics['parameter_c6'] = len(param_metrics) * [row['c6']]
            param_metrics['parameter_cidr_max4'] = len(param_metrics) * [row['cidr4']]
            param_metrics['parameter_cidr_max6'] = len(param_metrics) * [row['cidr6']]
            param_metrics['parameter_t'] = len(param_metrics) * [row['t']]
            param_metrics['parameter_e'] = len(param_metrics) * [row['e']]
            param_metrics['parameter_decay'] = len(param_metrics) * [row['decay']]
            param_metrics['parameter_study_name'] = len(param_metrics) * [para]
            param_metrics['parameter_study_type'] = len(param_metrics) * [study]
            param_metrics.reset_index(inplace=True)
            param_metrics.drop('index', axis=1, inplace=True)

            metrics: pd.DataFrame = pd.concat([metrics, param_metrics])

        metrics.to_csv(f'data/metrics.csv', index=False, header=None)
    print(f'\tmetric lines: {len(metrics)}')
    print(f'\t#Parameterizations: {len(metrics["parameter_study_name"].unique())}')
    print('----- CALCULATE FINISHED -----')


def calc_stability() -> None:
    '''calculate the stability for all parametrizations'''
    print('----- SETUP STABILITY -----')
    with Spinner():
        for _, row in parametrizations.iterrows():
            para: str = (f"q{row['q']}_c{row['c4']}-{row['c6']}_cidr_max{row['cidr4']}-{row['cidr6']}_t{row['t']}"
                         f"_e{row['e']}_decay{row['decay']}")
            os.system(f'stability/calculate_prefix_stability.sh {para} mini_internet')

    print('----- CALCULATE STABILITY -----')
    with Spinner():
        for _, row in parametrizations.iterrows():
            para: str = (f"q{row['q']}_c{row['c4']}-{row['c6']}_cidr_max{row['cidr4']}-{row['cidr6']}_t{row['t']}"
                         f"_e{row['e']}_decay{row['decay']}")
            get_data(para, 'mini_internet')

    print('----- CONNECT STABILITY RESULTS -----')
    with Spinner():
        connect('mini_internet')


def main() -> None:
    # create tables if not exist
    os.system('clickhouse-client --multiquery < queries/create_tables.sql')
    insert_into_clickhouse()
    calc_metrics()
    calc_stability()
    os.system('bash ./insert_metrics.sh')


if __name__ == '__main__':
    main()

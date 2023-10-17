#!/usr/bin/python3

import os
import csv
import glob
import numpy as np
import pandas as pd

from itertools import product
from clickhouse_driver import Client


__author__ = 'Max Bergmann'


MIN_STABLE_SECONDS: int = 300  # 5 min

DIR: str = '/home/bergmmax/WORK/masterthesis/pipeline/data/stabilities/'

client: Client = Client('localhost')  # for executing the queries

filter: list = ['network_full_all', 'network_full_all', 'network_full_all', 'ipd_full_all']

duration: str = 'sec'

# databases/tables to get data from
dbs: dict = {
    'network': 'max.netstability_2_mini_internet',
    'ipd': 'max.aggregate_netid_ingress__mv_bundles_mini_internet'
}

analysis_types: list = ['network', 'ipd']
granularities: list = ['full']
data_types: list = ['all']

combinations: list = list(product(analysis_types, granularities, data_types))


def get_data(para: str, study_type: str) -> None:
    '''
    reads the data from the database from given tables and saves them to csv for later use

    Arguments
    ---------
    para (str): identification string of parametrization
    study_type (str): identification string of study to use as reference
    '''
    print(f'----- GET DATA FOR: {para}')
    for analysis_type, granularity, data_type in combinations:

        db: str = dbs[analysis_type]
        output_folder: str = f'{DIR}/{analysis_type}_{granularity}_{data_type}/'
        os.makedirs(output_folder, exist_ok=True)

        granulary_staement: str = ''

        if analysis_type == 'ipd':
            select_statement: str = 'length_seconds'
        elif analysis_type == 'network':
            select_statement: str = 'network_stable_timed'

        if duration == 'sec':
            duration_statemant: str = f'{select_statement}'
        elif duration == 'min':
            duration_statemant: str = f'{select_statement} /60'
        elif duration == 'h':
            duration_statemant: str = f'{select_statement} /3600'

        top21_statement: str = ''
        if data_type == 'top21':
            top21_statement: str = '''
            AND (toDate(t), netid_string) IN
                (
                    SELECT t, netid_string
                    FROM ipd.prefix_asn
                    -- TOP21 ASNs that carry 80 percent of traffic (on 17.11.2020)
                    WHERE asn IN ['15169', '2906', '20940', '6805', '32934', '16509', '202818', '46489', '65050',
                                '22822', '65013', '15133', '6185', '24940', '54113', '20446', '60068', '16276',
                                '13335', '5483', '32590']
                )
            '''

        # mask_statement: str = 'and mask <= 16'  # TODO: 22, 23 oder raus nehmen
        mask_statement: str = ''  # TODO

        no_data_filter_statement: str = f' and length_seconds > {MIN_STABLE_SECONDS}'
        if analysis_type == 'network':
            no_data_filter_statement: str = (f' and network_stable_timed > {MIN_STABLE_SECONDS} and'
                                             f' no_data_events_length_seconds < 2592000')

        query: str = f'''
            select
                state_length as duration,
                occurrences,
                cumsum,
                cdf,
                pdf,
                ccdf,
                totals
            from (
                select
                    groupArray(state_length) as arr__state_length,
                    groupArray(occurrences) as arr__occurrences,
                    arrayReduce('sum', arr__occurrences) as totals,
                    arrayCumSum(arr__occurrences) as arr__occurrences_cumsum,
                    arrayMap(x -> x / totals, arr__occurrences_cumsum) as arr_cdf,
                    arrayMap(x -> 1-(x / totals), arr__occurrences_cumsum) as arr_ccdf,
                    arrayMap(x -> x / totals, arr__occurrences) as arr_pdf
                from (
                    select
                        state_length,
                        occurrences
                    from (
                        select
                            -- could be used directly. coarsening helps lowering amount of buckets.
                            round({duration_statemant}, 0) as state_length,
                            count() as occurrences
                        from
                            {db}
                        where
                            ingress_router <> 'NO_DATA'
                            and parameter_study_name == '{para}'
                            and parameter_study_type == '{study_type}'
                            and {select_statement} > 0
                            {top21_statement}
                            {granulary_staement}
                            {mask_statement}
                            -- {no_data_filter_statement}  -- TODO RAUS NEHMEN
                        group by
                            state_length
                        order by
                            state_length
                    )
                    --where
                        --state_length < 100000  -- a day would be 86'400 seconds --> this is with a little buffer
                        -- and state_length >= 300  -- longer than 5 min
                    order by state_length WITH FILL FROM 300 TO 100000 STEP 300
                )
            )
            array join
                arr__state_length as state_length,
                arr__occurrences as occurrences,
                arr__occurrences_cumsum as cumsum,
                arr_cdf as cdf,
                arr_ccdf as ccdf,
                arr_pdf as pdf
            '''

        res: list = client.execute(query)
        # print(pd.DataFrame(res))
        if np.isnan(res).any():
            print(f'        check results of {para}')

        with open(f'{output_folder}/{para}_all_{duration}.csv', 'w') as out:
            csv_out = csv.writer(out)
            csv_out.writerow(['duration', 'occurences', 'cumsum', 'cdf', 'pdf', 'ccdf', 'totals'])
            csv_out.writerows(list(map(list, res)))

    print('----- GET DATA FINISHED -----')


def connect(study: str) -> None:
    '''
    connects stability metric for all calculated stability values for given study

    Arguments
    ---------
    study (str): identification string of study
    '''
    folders: list = ['ipd_full_all', 'network_full_all']

    start_index: int = 3
    end_index: int = 288

    columns_durations: list = [str(t) for t in np.arange(1200, 86700, 300)]

    metrics: pd.DataFrame = pd.DataFrame(
        columns=columns_durations + [
            'parameter_q',
            'parameter_c4',
            'parameter_c6',
            'parameter_cidr_max4',
            'parameter_cidr_max6',
            'parameter_t',
            'parameter_e',
            'parameter_decay',
            'definition',
            'parameter_study_name',
            'parameter_study_type',
        ]
    )

    for folder in folders:
        files: list = glob.glob(f'{DIR}/{folder}/*.csv')

        for file in files:
            params: str = file.split('/')[-1].split('_all_sec.csv')[0]
            cdf: list = pd.read_csv(file)['cdf'][start_index:end_index].to_list()

            q: str = params.split('_')[0][1:]
            c4: str = params.split('_')[1].split('-')[0][1:].split('.')[0]
            c6: str = params.split('_')[1].split('-')[1].split('.')[0]
            cidr4: str = params.split('_')[3].split('-')[0][3:]
            cidr6: str = params.split('_')[3].split('-')[1]
            t: str = params.split('_')[4][1:]
            e: str = params.split('_')[5][1:]
            decay: str = params.split('_')[6][5:]

            basic: list = cdf + [q, c4, c6, cidr4, cidr6, t, e, decay, folder, params, study]
            metrics.loc[len(metrics)] = basic

    metrics.to_csv(
        f'/home/bergmmax/WORK/masterthesis/pipeline/data/metrics_stability.csv',
        index=False,
        header=None
    )

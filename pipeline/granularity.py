#!/usr/bin/python3

import pandas as pd

from helper import CLIENT
from helper import get_query_w_columns


__author__ = 'Max Bergmann'


def get_granularity(params: str) -> pd.DataFrame:
    '''
    calculates the granularity (+ normed between 0 and 1) for each timestep for given parametrization'

    Arguments
    ----------
    params (int): string of the parametrization

    Returns
    ----------
    gran_frame (DataFrame): returns table with calculated granularities and numbers for calculation
    '''
    query, columns = get_query_w_columns('mask_occ_ts', params)

    # get the number of occurence per mask per timestep
    data: list = CLIENT.execute(query)
    num_mask: pd.DataFrame = pd.DataFrame(data, columns=columns)

    # calculate the number of classified IPv4 addresses per timestep from mask and count
    num_ips: list = [
        (count * (2 ** (32 - mask)))
        for mask, count
        in zip(num_mask['mask'], num_mask['count'])
    ]
    num_mask['num_ips'] = num_ips

    full_addressspace: int = 2 ** 32  # number of addresses in full IPv4 Addressspace
    timesteps: list = list(num_mask.groupby(by='timestep')['count'].sum().index)  # distinct timesteps
    prefix_count: list = list(num_mask.groupby(by='timestep')['count'].sum().values)  # number of prefix per timestep
    # number of classified IPv4 addresses per timestep
    classified_addresses: list = list(num_mask.groupby(by='timestep')['num_ips'].sum().values)

    gran_frame: pd.DataFrame = pd.DataFrame(
        data={
            'timestep': timesteps,
            'prefix_count': prefix_count,
            'classified_addresses': classified_addresses
        },
        columns=['timestep', 'prefix_count', 'classified_addresses']
    )
    if len(gran_frame) >= 2:
        # remove first 2 timesteps because of possible demaged data and high granularity
        gran_frame.drop([0, 1], inplace=True)

    # calculate the relative share of classified IP addresses to full addressspace for each timestep
    gran_frame['rel_share'] = [
        clas_add / full_addressspace
        for clas_add
        in gran_frame['classified_addresses']
    ]

    # calculate the granularity by relative share / prefix count
    gran_frame['granularity'] = [
        r_share / p_count
        for r_share, p_count
        in zip(gran_frame['rel_share'], gran_frame['prefix_count'])
    ]
    # norm granularity between 0 and 1
    gran_frame['granularity_normed'] = gran_frame['granularity']/gran_frame['granularity'].abs().max()

    return gran_frame

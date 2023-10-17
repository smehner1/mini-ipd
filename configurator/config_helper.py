#!/usr/bin/python3

import numpy as np
import pandas as pd

from typing import Tuple

__author__ = 'Max Bergmann'


HOLE_ROUTERS: list = ['NEWY', 'SANF']  # routers in around ASs that are used for egress from AS 1
EGRESS_LINKS: list = [('COTT', 'NEWY', 2), ('NEWY', 'NEWY', 3), ('SANF', 'SANF', 4), ('SAOP', 'SANF', 5)]

CENTER_AS: int = 1


def get_links(minidir: str) -> pd.DataFrame:
    '''
    get links Dataframe representing connection from what AS and router to what AS and router using what IP

    Arguments
    ---------
    minidir (str): path to Mini-Internet directory

    Returns
    -------
    links (DataFrame): connections between ASes
    '''
    external_links: str = f'{minidir}/config/external_links_config.txt'

    links: pd.DataFrame = pd.read_csv(external_links, header=None, sep=' ')
    links.columns = ['id1', 'router1', '_', 'id2', 'router2', '__', '___', '____', 'ip']
    links.drop(['__', '___', '____', '_'], axis=1, inplace=True)

    return links


def get_routers_info(minidir: str) -> pd.DataFrame:
    '''
    gives the pandas dataframe with the names of routers in each AS in Mini-Internet

    Arguments
    ---------
    minidir (str): path to directory of mini-internet

    Returns
    -------
    routers_info (DataFrame): frame with names of routers within each AS
    '''
    router_file: str = f'{minidir}/config/router_config_full.txt'
    routers_info: pd.DataFrame = pd.read_csv(router_file, header=None, sep=' ')
    routers_info.columns = ['name', '_', '__', '___']

    return routers_info


def extract_infos(minidir: str) -> Tuple[int, list, dict]:
    '''
    extracts the number of routers, the ASs used in mini-internet and a map of routers in center AS and the connected
    routers arround

    Returns
    --------
    num_routers (int): number of routers within each AS
    ases (list(int)): list with identifier numbers of ASs around center AS
    edges (dict): dictionary that maps arround AS number to routers within center AS to routers in arround AS
    '''
    num_routers: int = len(get_routers_info(minidir))  # number of routers per AS
    ases: list = np.arange(2, get_links(minidir)['id1'].max()+1, 1)  # list of AS identifiers around center-AS
    all_routers: list = get_routers_info(minidir)['name'].to_list()  # names of all routers within each AS

    edges: dict = {}
    as1_connections: pd.DataFrame = get_links(minidir).query('id1 == 1')

    for AS in ases:
        for router in all_routers:
            router_connections: pd.DataFrame = as1_connections.query(f'router1 == "{router}" and id2 == {AS}')
            for i in range(len(router_connections)):
                row: pd.Series = router_connections.iloc[i]

                # extract intern infos
                if str(AS) in edges.keys():
                    if row.router1 not in edges[str(AS)].keys():
                        edges[str(AS)][row.router1] = [row.router2]
                    else:
                        edges[str(AS)][row.router1].append(row.router2)
                else:
                    edges[str(AS)] = {row.router1: [row.router2]}

    return num_routers, ases, edges

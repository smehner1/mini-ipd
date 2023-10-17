#!/usr/bin/python3

import os
import sys
import time
import random
import argparse
import numpy as np
import pandas as pd

from netaddr import IPNetwork
from datetime import datetime

from generate_scapy_configs import generate_daily_configs, generate_config_router


__author__ = 'Max Bergmann'


CENTER_AS: int = 1

# distribution from day curve of decix munich
diurnal_pattern: list = [
    50, 44, 37, 37, 52, 87, 131, 165, 168, 164, 148, 142, 166, 155, 144, 133, 118, 117, 123, 139, 135, 120, 91, 65
]
# relative share, where maximum number will give the max_flows
diurnal_pattern_relative: list = [x/max(diurnal_pattern) for x in diurnal_pattern]


def init_parser() -> argparse.ArgumentParser:
    '''initializes a parser for the CLI'''
    parser = argparse.ArgumentParser()
    parser.add_argument('--start',
                        help='flag to define if to start or stop scapy processes',
                        action='store_true',
                        )
    parser.add_argument('--kill', dest='start', action='store_false')
    parser.add_argument('--dir',
                        help='path to directory of mini internet',
                        type=str,
                        default='/home/max/WORK/mini-internet/',
                        )
    parser.add_argument('--sharedir',
                        help='path to directory of mini internet',
                        type=str,
                        default='/home/host_files/',
                        )
    parser.add_argument('--sharedirlocal',
                        help='path to directory of shared files in container',
                        default='/home/max/WORK/masterthesis/mini_internet/host_files/',
                        type=str,
                        )
    parser.add_argument('-g',
                        help='flag to define if connections need to be generated',
                        action='store_true',
                        )
    parser.add_argument('-n',
                        help='noise to generate for each as',
                        type=float,
                        default=0.1
                        )
    parser.add_argument('-w',
                        help='seconds to run 1 hour traffic in (example: 10 min => 4 h capturing for 1 day netflow)',
                        type=int,
                        default=180
                        )
    parser.add_argument('-f',
                        help='maximum number of flows to generate in an hour',
                        type=int,
                        default=5000
                        )
    parser.add_argument('-o',
                        help='inidicate overflow when setting to not 0 (if not 0 than identifier of AS)',
                        type=int,
                        default=0
                        )
    parser.add_argument('-ot',
                        help='number of as to send overflow to',
                        default=3,
                        type=int,
                        )
    parser.set_defaults(start=True, g=False)

    return parser


def start_as_traffic(
        iteration: int,
        router_file: str,
        net: int,
        noise: float,
        sharedir: str,
        overflow: bool = False
        ) -> None:
    '''
    starts the traffic from given AS with possible noise and possible overflow event

    Arguments
    ---------
    iteration (int): iteration to start traffic for
    router_file (str): path to file of router configs in Mini-Internet
    net (int): identifier of AS to start traffic from
    noise (float): portion of noise to generate
    sharedir (str): directory of mounted folder of hosts including run_pakets.py
    overflow (bool): set to true, if this  network is included in an overflow event
    '''
    print(f'----- Start Traffic in AS {net} -----')

    routers_info: pd.DataFrame = pd.read_csv(router_file, header=None, sep=' ')
    routers_info.columns = ['name', '_', '__', '___']

    routers: list = routers_info['name'].to_list()
    for i in range(len(routers)):
        if overflow:
            cmd: str = (f'docker exec -d {net}_{routers[i]}host bash -c "python3 {sharedir}/run_pakets.py -a {net} -r '
                        f'{i+1} -i {iteration} -n {noise} -o -t 5"')
        else:
            cmd: str = (f'docker exec -d {net}_{routers[i]}host bash -c "python3 {sharedir}/run_pakets.py -a {net} -r '
                        f'{i+1} -i {iteration} -n {noise} -t 15"')
        os.popen(cmd)


def stop_as_traffic(net: int) -> None:
    '''
    stops all traffic generated from given AS

    Arguments
    ---------
    net (int): identification number of AS to stop the traffic from
    '''
    awk: str = "awk '{print $2}'"
    os.popen(f"ps -ef | grep \"run_pakets.py -a {net}\" | grep -v grep | {awk} | sudo xargs kill")


def create_overflow_iteration(
        pref: str,
        offpref: str,
        iteration: int,
        dir: str,
        sharedir: str,
        n1: int,
        n2: int,
        p: float
) -> None:
    '''
    uses general configurations and offloads flows from one AS to another by removing and adding configurations

    Arguments
    ---------
    pref (str): the original prefix that includes the offloading prefix
    offpref (str): the offloading prefix as subnet of pref
    iteration (int): iteration to offload the prefix
    dir (str): path to Mini-Internet
    sharedir (str): path to shared/mounted folder of host containers
    n1 (int): identifier of source AS
    n2 (int): identifier of target AS
    p (float): portions of flows to offload
    '''
    # generate ip addresses from old address space
    ips: IPNetwork = IPNetwork(pref)
    list_ips: list = list(ips)[1:-1]
    list_ips: list = [str(x.ipv4()) for x in list_ips]

    # generate ip addresses from offload address space
    ips: IPNetwork = IPNetwork(offpref)
    list_ips_2: list = list(ips)[1:-1]
    list_ips_2: list = [str(x.ipv4()) for x in list_ips_2]
    list_ips = [x for x in list_ips if x not in list_ips_2]

    # read actual configs of src and dst AS
    connections_frame_src = pd.read_csv(
            f'{sharedir}/connections_{n1}.csv',
        )
    connections_frame_src.sort_values(['iteration', 'src', 'sip'], inplace=True)
    connections_frame_src.to_csv(
            f'{sharedir}/connections_{n1}.csv',
            index=False,
        )
    connections_frame_dst = pd.read_csv(
            f'{sharedir}/connections_{n2}.csv',
        )
    connections_frame_dst.sort_values(['iteration', 'src', 'sip'], inplace=True)
    connections_frame_dst.to_csv(
            f'{sharedir}/connections_{n2}.csv',
            index=False,
        )

    # get old connections of overflow iteration
    iteration_flows_src = len(connections_frame_src.query(f'iteration == {iteration}'))
    offload_flow_number: int = int(iteration_flows_src*p)

    # remove the offload ips froim source AS traffic
    for ip in list_ips_2:
        connections_frame_src.drop(
            connections_frame_src.query(f'sip=="{ip}" and iteration=={iteration}').index,
            inplace=True
        )

    as_file: str = f'{dir}/platform/config/AS_config.txt'
    as_info: pd.DataFrame = pd.read_csv(as_file, sep=' ', header=None)
    as_info.columns = ['id', '_', '__', '___', '____', '_____', '______', '_______']
    target_ases: list = as_info['id'].to_list()

    offload_connections: list = generate_config_router(offpref, offload_flow_number, target_ases, iteration)
    connections_frame_dst = pd.concat([
        connections_frame_dst,
        pd.DataFrame(offload_connections, columns=connections_frame_dst.columns)
    ])

    connections_frame_src.sort_values(['iteration', 'src', 'sip'], inplace=True)
    connections_frame_dst.sort_values(['iteration', 'src', 'sip'], inplace=True)
    connections_frame_src.to_csv(
            f'{sharedir}/connections_{n1}.csv',
            index=False
        )
    connections_frame_dst.to_csv(
            f'{sharedir}/connections_{n2}.csv',
            index=False
        )


def get_expected_iteration_flows(iteration: int) -> int:
    '''
    return the generated flows of given iteration

    Arguments
    ---------
    iteration (int): iteration to get flows of

    Returns
    -------
    flows (int): number of flows to generate
    '''
    flows: int = 0

    for i in [2, 3, 4, 5]:
        connections: pd.DataFrame = pd.read_csv(
            f'/home/max/WORK/masterthesis/mini_internet/host_files/connections_{i}.csv')
        flows += len(connections.query(f'iteration == {iteration}'))

    return flows


def start_daily_traffic() -> None:
    '''generates configurations for 24 iterations including possible hypergiants and offloadings'''
    parser: argparse.ArgumentParser = init_parser()
    args: argparse.Namespace = parser.parse_args()

    router_file: str = f'{args.dir}/platform/config/router_config_full.txt'

    if args.start:  # start scapy processes
        if '.py' in __file__.split('/')[0]:
            portions: pd.DataFrame = pd.read_csv('configs/as_traffic_distro.csv')
        else:
            portions: pd.DataFrame = pd.read_csv(
                f'{__file__.split("traffic_controller")[0]}/configs/as_traffic_distro.csv')
        portions.columns: list = ['net', 'portion']

        as_file: str = f'{args.dir}/platform/config/AS_config.txt'
        as_info: pd.DataFrame = pd.read_csv(as_file, sep=' ', header=None)
        as_info.columns = ['id', '_', '__', '___', '____', '_____', '______', '_______']
        target_ases: list = as_info['id'].to_list()
        source_ases: list = [net for net in target_ases if net != CENTER_AS]

        if args.g:
            # clear existing files and cofigs
            for net in source_ases:
                clear_df: pd.DataFrame = pd.DataFrame(
                    [],
                    columns=['iteration', 'src', 'sip', 'dst', 'dip', 'router', 'sport', 'dport'])
                clear_df.to_csv(
                    f'/home/max/WORK/masterthesis/mini_internet/host_files/connections_{net}.csv',
                    index=False
                )

            start = datetime.now()
            # generate flows per hour of day
            for i in range(len(diurnal_pattern_relative)):
                r: int = diurnal_pattern_relative[i]
                error: bool = generate_daily_configs(
                    i,
                    int(args.f*r),
                    portions,
                    target_ases,
                    source_ases,
                    args.sharedirlocal,
                    True,  # change to true for hypergiant
                )
                if error:
                    print('|-> STOPPING traffic generator !')
                    sys.exit(1)

            if args.o != 0:
                for i in np.arange(15, 18, 1):
                    create_overflow_iteration(
                        '2.101.0.0/24',
                        '2.101.0.0/28',
                        i,
                        args.dir,
                        args.sharedirlocal,
                        2,
                        5,
                        random.choice([0.1, 0.2, 0.3])
                    )
                for i in np.arange(8, 11, 1):
                    create_overflow_iteration(
                        '3.105.0.0/24',
                        '3.105.0.0/28',
                        i,
                        args.dir,
                        args.sharedirlocal,
                        3,
                        4,
                        random.choice([0.1, 0.2, 0.3])
                    )
            end = datetime.now()
            print(f'Time to generate configs: {end-start}')
            time.sleep(2)

        # start the traffic for corresponding time interval
        starttime: datetime = time.monotonic()
        for i in range(24):
            start = datetime.now()
            r: int = diurnal_pattern_relative[i]
            # print(f'Start iteration {i} at: {start} with {int(args.f*r)} flows')
            with open('time.log', 'a') as file:
                file.write(f'{args.n}/{i}: {str(start)}\n')
            print(f'Start iteration {i} at: {start} with {get_expected_iteration_flows(i)} flows')
            # for net in [2, 3]:
            for net in source_ases:
                if i != 0:
                    # stop traffic in net
                    stop_as_traffic(net)
                    time.sleep(1)
                # start traffic for hour i in net
                start_as_traffic(i, router_file, net, args.n, args.sharedir)
                time.sleep(1)
            end = datetime.now()
            print(f'Start iteration starting {i} after {end-start} seconds\n')

            waiting = args.w - ((time.monotonic() - starttime) % args.w)
            time.sleep(waiting)

        print('FINISHED TRAFFIC -> stop all packet sender')
        for net in source_ases:
            stop_as_traffic(net)

        time.sleep(1*60)  # wait 3 minutes to ensure the netflow collector has collected the last iteration completely

        print('KILL NETFLOW COLLECTOR')
        os.popen("ps -ef | grep netflow_collector.py| grep -v grep | awk '{print $2}' | sudo xargs kill")
    else:  # stop all run_pakets.py processes
        os.popen("ps -ef | grep run_pakets.py | grep -v grep | awk '{print $2}' | sudo xargs kill")


def main() -> None:
    '''generates traffic for one iteration'''
    parser: argparse.ArgumentParser = init_parser()
    args: argparse.Namespace = parser.parse_args()

    external_links: str = f'{args.dir}/platform/config/external_links_config.txt'
    router_file: str = f'{args.dir}/platform/config/router_config_full.txt'

    if args.start:  # start scapy processes
        links: pd.DataFrame = pd.read_csv(external_links, header=None, sep=' ')
        links.columns = ['id1', 'router1', '_', 'id2', 'router2', '__', '___', '____', 'ip']
        links.drop(['__', '___', '____', '_'], axis=1, inplace=True)
        ases: list = np.arange(2, links['id1'].max()+1, 1)  # list of AS identifiers around center-AS

        for net in ases:
            start_as_traffic(0, router_file, net, args.n, args.sharedir)
            time.sleep(1)
    else:  # stop all run_pakets.py processes
        os.popen("ps -ef | grep run_pakets.py | grep -v grep | awk '{print $2}' | sudo xargs kill")


if __name__ == '__main__':
    main()
    # start_daily_traffic()

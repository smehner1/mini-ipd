#!/usr/bin/python3

import os
import random
import argparse
import numpy as np
import pandas as pd

from netaddr import IPNetwork

__author__ = 'Max Bergmann'


random.seed(2212976604)  # add a seed for pseudo randomness

CENTER_AS: int = 1  # AS that runs the IPD

POS_TARGETS: list = np.arange(1, 255, 1)
POS_ROUTERS: list = np.arange(101, 109, 1)
POS_PORTS: list = np.arange(1024, 65535, 1).tolist()

mapping: dict = {
    101: [1, 2],
    102: [1, 2],
    103: [3, 4],
    104: [3, 4],
    105: [5, 6],
    106: [5, 6],
    107: [7, 8],
    108: [7, 8],
}


def init_parser() -> argparse.ArgumentParser:
    '''initializes a parser for the CLI'''
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir',
                        help='path to directory of mini internet',
                        type=str,
                        default='../mini-internet/',
                        )
    parser.add_argument('--sharedir',
                        help='path to directory of shared files in container',
                        default='../shared_directories/host_files/',
                        type=str,
                        )
    parser.add_argument('-t',
                        help='target flow number',
                        default=5000,
                        type=int,
                        )
    parser.add_argument('-c',
                        help='config file that includes the portions of produced traffic',
                        default='configs/as_traffic_distro.csv',
                        type=str,
                        )
    parser.add_argument('--hyper',
                        help='set to true if some prefixes shall interact like a hypergiant from hypergiants.csv',
                        default=False,
                        type=bool,
                        )

    return parser


def generate_daily_configs(
        iteration: int,
        target_flows: int,
        portions: pd.DataFrame,
        target_ases: list,
        source_ases: list,
        shared_dir: str,
        hyper: bool = False,
) -> bool:
    '''
    will generate src, dst mappings that generates the specified number of flows per AS with random ports. each router
    will send traffic to the same router within another AS, to control prefix ingress

    Arguments
    ----------
    target_flows (int): number of flows to generate for trafficgenerate_day_traffic.sh
    portions (DataFrame): portions of traffic to produce per AS
    target_ases (list): list of AS identifier numbers to send traffic to
    source_ases (list): list of AS identifier numbers to send traffic from
    shared_dir (str): path to shared directory of host container

    Returns
    -------
    error (bool): sets to True if error occured while generating
    '''
    target_flows_dict: dict = {}  # will include the target flow for each AS to add missing at the end

    if '.py' in __file__.split('/')[0]:
        hypergiants: pd.DataFrame = pd.read_csv('configs/hypergiants.csv')
    else:
        hypergiants: pd.DataFrame = pd.read_csv(
            f'{__file__.split("generate_scapy_configs")[0]}/configs/hypergiants.csv')

    # check if hypergiants config does not exceed overall 100% of traffic
    iterations: np.ndarray = hypergiants['iteration'].unique()
    for iter in iterations:
        iter_frame: pd.DataFrame = hypergiants.query(f'iteration=={iter}')
        hypergiant_ratio: float = iter_frame['ratio'].sum()
        if hypergiant_ratio > 1:  # hypergiants take more than full traffic
            print(f'ERROR: Hypergiants for iteration {iter} take more than 100% of netflow!')
            return True

    for net in source_ases:
        connections_frame: pd.DataFrame = pd.read_csv(
            f'{shared_dir}/connections_{net}.csv')

        connections: list = []  # will include the mapping from source to target
        net_portion: float = portions.query(f'net == {net}').iloc[0]['portion']  # read portion of full traffic
        net_flows: int = int(round(net_portion * target_flows, 0))  # calculate the flow for this net
        target_flows_dict[net] = net_flows

        num_hyper_conns = 0
        used_hyper_ips = []
        if hyper and net in hypergiants['net'].unique():
            hyper_conns = hypergiants.query(f'net=={net} and iteration=={iteration}')
            for index, row in hyper_conns.iterrows():
                num_hyper_flows = row['ratio'] * target_flows
                hyper_prefix = row['prefix']
                router = int(hyper_prefix.split('.')[1])
                hyper_ips: IPNetwork = IPNetwork(hyper_prefix)
                list_hyper_ips: list = list(hyper_ips)[1:-1]
                list_hyper_ips: list = [
                    str(x.ipv4()) for x in list_hyper_ips if str(x.ipv4()) != f'{hyper_prefix.split(".0/")[0]}.2'
                ]
                pos_ports: list = POS_PORTS.copy()
                hyper_ips = used_hyper_ips + list_hyper_ips

                for _ in range(int(num_hyper_flows/2)):
                    src_ip = random.choice(list_hyper_ips)  # chose src ip
                    target: int = random.choice([x for x in target_ases if x != net])  # choose random target AS

                    # randomly choose src and dst port and remove for unique flows
                    sport: int = random.choice(pos_ports)
                    pos_ports.remove(sport)
                    dport: int = random.choice(pos_ports)
                    pos_ports.remove(dport)
                    # generate target as with first target router
                    dst_router1 = mapping[router][0]
                    address1 = f'{target}.10{dst_router1}.0.1'
                    connections.append([iteration, net, src_ip, target, address1, int(str(router)[-1]), sport, dport])

                    # randomly choose src and dst port and remove for unique flows
                    sport: int = random.choice(pos_ports)
                    pos_ports.remove(sport)
                    dport: int = random.choice(pos_ports)
                    pos_ports.remove(dport)
                    # generate target as with second target router
                    dst_router2 = mapping[router][1]
                    address2 = f'{target}.10{dst_router2}.0.1'
                    connections.append([iteration, net, src_ip, target, address2, int(str(router)[-1]), sport, dport])
                    num_hyper_conns += 2

        net_flows -= num_hyper_conns
        # calculate flows for each router in this AS (divided by 2 to send to 2 dst routers -> mapping)
        portion_flows: int = int(net_flows/len(POS_ROUTERS)/2)

        for router in POS_ROUTERS:
            pos_ports: list = POS_PORTS.copy()
            # generate src ip address pool
            prefix: str = f'{net}.{router}.0.0/24'
            ips: IPNetwork = IPNetwork(prefix)
            list_ips: list = list(ips)[1:-1]
            # remove the router IP and all hypergiant IPs
            list_ips: list = [
                str(x.ipv4()) for x in list_ips if str(x.ipv4()) != f'{net}.{router}.0.2' and
                str(x.ipv4()) not in used_hyper_ips
            ]

            if list_ips != []:
                for _ in range(portion_flows):
                    src_ip = random.choice(list_ips)  # chose src ip
                    target: int = random.choice([x for x in target_ases if x != net])  # choose random target AS

                    # randomly choose src and dst port and remove for unique flows
                    sport: int = random.choice(pos_ports)
                    pos_ports.remove(sport)
                    dport: int = random.choice(pos_ports)
                    pos_ports.remove(dport)
                    # generate target as with first target router
                    dst_router1 = mapping[router][0]
                    address1 = f'{target}.10{dst_router1}.0.1'
                    connections.append([iteration, net, src_ip, target, address1, int(str(router)[-1]), sport, dport])

                    # randomly choose src and dst port and remove for unique flows
                    sport: int = random.choice(pos_ports)
                    pos_ports.remove(sport)
                    dport: int = random.choice(pos_ports)
                    pos_ports.remove(dport)
                    # generate target as with second target router
                    dst_router2 = mapping[router][1]
                    address2 = f'{target}.10{dst_router2}.0.1'
                    connections.append([iteration, net, src_ip, target, address2, int(str(router)[-1]), sport, dport])

        connections_frame = pd.concat([connections_frame, pd.DataFrame(
            connections, columns=['iteration', 'src', 'sip', 'dst', 'dip', 'router', 'sport', 'dport'])])

        # if not all flows where created additionally add some randomly more
        extras: int = int(target_flows_dict[net]-len(connections))
        extra_conns: list = []
        for _ in range(extras):
            dst_as: int = random.choice(target_ases)
            dst_as: int = random.choice([x for x in target_ases if x != net])
            router: int = random.choice(POS_ROUTERS)
            host: int = random.choice(POS_TARGETS)
            sport: int = random.choice(POS_PORTS)
            dport: int = random.choice(POS_PORTS)

            src_ip: str = f'{net}.{router}.0.{host}'

            while src_ip in used_hyper_ips:
                router: int = random.choice(POS_ROUTERS)
                src_ip: str = f'{net}.{router}.0.1'

            dst_ip: str = f'{dst_as}.{router}.0.1'

            extra_conns.append([iteration, net, src_ip, dst_as, dst_ip, int(str(router)[-1]), sport, dport])

        connections_frame: pd.DataFrame = pd.concat([
            pd.DataFrame(extra_conns, columns=['iteration', 'src', 'sip', 'dst', 'dip', 'router', 'sport', 'dport']),
            connections_frame
        ])

        connections_frame.sort_values(['iteration', 'src', 'sip'], inplace=True)
        connections_frame.to_csv(
            f'{shared_dir}/connections_{net}.csv',
            index=False
        )

    return False


def generate_config_router(
        prefix: str,
        target_flows: int,
        target_ases: list,
        iteration: int = 0,
) -> list:
    '''
    generates the scapy configurations for a given specific router (extracted from prefix)

    Arguments
    ---------
    prefix (str): the prefix of the router to send from
    target_flows (int): number of flows to send from this router
    target_ases (list): list of AS identifiers that can traffic send to
    iteration (int): iteration to generate the connections for (default = 0)

    Returns
    -------
    connections (list): list of all connections from given router to random other ASes and routers
    '''
    pos_ports: list = POS_PORTS
    connections: list = []  # will include the mapping from source to target
    # generate src ip address pool
    ips: IPNetwork = IPNetwork(prefix)
    list_ips: list = list(ips)[1:-1]
    router_ip = prefix.split('/')[0]
    router_ip = router_ip[:-1] + '2'

    router = int(prefix.split('/')[0].split('.')[1])
    net = int(prefix.split('/')[0].split('.')[0])

    list_ips: list = [str(x.ipv4()) for x in list_ips if str(x.ipv4()) != router_ip]

    for _ in range(int(target_flows/2)):
        src_ip = random.choice(list_ips, )  # chose src ip
        target: int = random.choice([x for x in target_ases if x != net])  # choose random target AS

        # randomly choose src and dst port and remove for unique flows
        sport: int = random.choice(pos_ports)
        pos_ports.remove(sport)
        dport: int = random.choice(pos_ports)
        pos_ports.remove(dport)
        # generate target as with first target router
        dst_router1 = mapping[router][0]
        address1 = f'{target}.10{dst_router1}.0.1'
        connections.append([iteration, net, src_ip, target, address1, int(str(router)[-1]), sport, dport])

        # randomly choose src and dst port and remove for unique flows
        sport: int = random.choice(pos_ports)
        pos_ports.remove(sport)
        dport: int = random.choice(pos_ports)
        pos_ports.remove(dport)
        # generate target as with second target router
        dst_router2 = mapping[router][1]
        address2 = f'{target}.10{dst_router2}.0.1'
        connections.append([iteration, net, src_ip, target, address2, int(str(router)[-1]), sport, dport])

    # print(len(connections))
    return connections


def generate_configs(
        target_flows: int,
        portions: pd.DataFrame,
        target_ases: list,
        source_ases: list,
        shared_dir: str) -> None:
    '''
    will generate src, dst mappings that generates the specified number of flows per AS with random ports. each router
    will send traffic to the same router within another AS, to control prefix ingress

    Arguments
    ----------
    target_flows (int): number of flows to generate for traffic
    portions (DataFrame): portions of traffic to produce per AS
    target_ases (list): list of AS identifier numbers to send traffic to
    source_ases (list): list of AS identifier numbers to send traffic from
    shared_dir (str): path to shared directory of host container
    '''
    matrix: dict = {}  # will display which AS will send how many flows to what AS
    target_flows_dict: dict = {}  # will include the target flow for each AS to add missing at the end

    for net in source_ases:
        connections: list = []  # will include the mapping from source to target
        net_portion: float = portions.query(f'net == {net}').iloc[0]['portion']  # read portion of full traffic
        net_flows: float = net_portion * target_flows  # calculate the flow for this net
        target_flows_dict[net] = net_flows
        # calculate flows for each router in this AS (divided by 2 to send to 2 dst routers -> mapping)
        portion_flows: int = int(net_flows/len(POS_ROUTERS)/2)

        for router in POS_ROUTERS:
            pos_ports: list = POS_PORTS.copy()
            # generate src ip address pool
            prefix: str = f'{net}.{router}.0.0/24'
            ips: IPNetwork = IPNetwork(prefix)
            list_ips: list = list(ips)[1:-1]
            list_ips: list = [str(x.ipv4()) for x in list_ips if str(x.ipv4()) != f'{net}.{router}.0.2']

            for _ in range(portion_flows):
                src_ip = random.choice(list_ips)  # chose src ip
                target: int = random.choice([x for x in target_ases if x != net])  # choose random target AS

                # randomly choose src and dst port and remove for unique flows
                sport: int = random.choice(pos_ports)
                pos_ports.remove(sport)
                dport: int = random.choice(pos_ports)
                pos_ports.remove(dport)
                # generate target as with first target router
                dst_router1 = mapping[router][random.choice([0, 1])]
                address1 = f'{target}.10{dst_router1}.0.1'
                connections.append([0, net, src_ip, target, address1, int(str(router)[-1]), sport, dport])

                # randomly choose src and dst port and remove for unique flows
                sport: int = random.choice(pos_ports)
                pos_ports.remove(sport)
                dport: int = random.choice(pos_ports)
                pos_ports.remove(dport)
                # generate target as with second target router
                dst_router2 = mapping[router][1]
                address2 = f'{target}.10{dst_router2}.0.1'
                connections.append([0, net, src_ip, target, address2, int(str(router)[-1]), sport, dport])

        connections_frame: pd.DataFrame = pd.DataFrame(
            connections, columns=['iteration', 'src', 'sip', 'dst', 'dip', 'router', 'sport', 'dport'])

        # if not all flows where created additionally add some randomly more
        extra_conns: list = []
        for _ in range(int(target_flows_dict[net]-len(connections_frame))):
            dst_as: int = random.choice(target_ases)
            dst_as: int = random.choice([x for x in target_ases if x != net])
            router: int = random.choice(POS_ROUTERS)
            sport: int = random.choice(POS_PORTS)
            dport: int = random.choice(POS_PORTS)

            src_ip: str = f'{net}.{router}.0.1'
            dst_ip: str = f'{dst_as}.{router}.0.1'

            extra_conns.append([0, net, src_ip, dst_as, dst_ip, int(str(router)[-1]), sport, dport])

        connections_frame: pd.DataFrame = pd.concat([
            pd.DataFrame(extra_conns, columns=['iteration', 'src', 'sip', 'dst', 'dip', 'router', 'sport', 'dport']),
            connections_frame
        ])

        connections_frame.sort_values(['iteration', 'src', 'sip'], inplace=True)
        connections_frame.to_csv(
            f'{shared_dir}/connections_{net}.csv',
            index=False
        )

        # add connections to matrix for extra output
        ases = connections_frame['dst'].unique()
        matrix[net] = {}
        for n in ases:
            matrix[net][n] = int(len(connections_frame.query(f'dst=={n}')))

        print(f'{net}: {len(connections_frame)} Pakets ({connections_frame.duplicated().any()})')

    print()

    matrix_frame = pd.DataFrame(matrix)
    matrix_frame.sort_index(inplace=True)
    print(matrix_frame)
    matrix_frame.to_csv(f'{os.getcwd()}/{os.path.dirname(__file__)}/configs/matrix.csv')


def main() -> None:
    parser: argparse.ArgumentParser = init_parser()
    args: argparse.Namespace = parser.parse_args()

    target_flows: int = args.t
    config_file: str = args.c

    portions: pd.DataFrame = pd.read_csv(config_file)
    portions.columns = ['net', 'portion']

    as_file: str = f'{args.dir}/platform/config/AS_config.txt'
    as_info: pd.DataFrame = pd.read_csv(as_file, sep=' ', header=None)
    as_info.columns = ['id', '_', '__', '___', '____', '_____', '______', '_______']
    target_ases: list = as_info['id'].to_list()
    source_ases: list = [net for net in target_ases if net != CENTER_AS]

    # generate_configs(target_flows, portions, target_ases, source_ases, args.sharedir)
    generate_daily_configs(10, target_flows, portions, target_ases, source_ases, args.sharedir, args.hyper)


if __name__ == '__main__':
    main()

#!/usr/bin/python3

import os
import time
import argparse

from config_helper import extract_infos, HOLE_ROUTERS, get_links

__author__ = 'Max Bergmann'


def init_parser() -> argparse.ArgumentParser:
    '''initializes a parser for the CLI'''
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir',
                        help='path to directory of mini internet',
                        type=str,
                        default='../mini-internet/platform/',
                        )

    return parser


def configure_external_AS(announce_net: str, edges: dict, num_routers: int, minidir: str) -> None:
    '''
    announce the /24 prefixes from arround AS's to center AS with local prefs set to make center AS use the right
    egress link

    Arguments
    ---------
    announce_net (str): the identifier of the AS to announce the prefix's from to center AS
    edges (dict): dictionary that maps arround AS number to routers within center AS to routers in arround AS
    num_routers (int): number of routers within each AS
    minidir (str): path to mini internet directory
    '''
    connections: dict = edges[announce_net]
    routers_intern: list = connections.keys()

    for router_intern in routers_intern:
        routers_extern: list = connections[router_intern]

        for router_extern in routers_extern:
            cmd: str = f'sudo docker exec -ti {announce_net}_{router_extern}router bash -c "X"'
            vtysh_cmd: str = f"vtysh -c 'conf t' "

            # create prefix lists for all prefixes in external network
            for part in range(num_routers):
                vtysh_cmd += (f" -c 'ip prefix-list {announce_net}_{part} seq 10 permit {announce_net}.10{str(part+1)}."
                              f"0.0/24' ")

            # set preferences for egressing link
            if router_extern in HOLE_ROUTERS:
                loc_pref: str = '50000'
            else:
                loc_pref: str = '50'

            # create route-maps for external prefixes
            for j in range(num_routers):
                vtysh_cmd += f" -c 'route-map M_{announce_net} permit 10{str(j)}' "
                vtysh_cmd += f" -c 'match ip address prefix-list {announce_net}_{j}'"
                vtysh_cmd += f" -c 'set local-preference {loc_pref}' -c 'exit' "

            vtysh_cmd += f" -c 'router bgp {announce_net}' "

            # get ip between those routers to center AS
            ip: str = get_links(minidir).query((f'id1 == 1 and id2 == {announce_net} and router1 == "{router_intern}"'
                                                f' and router2 == "{router_extern}"')).iloc[0]['ip'].split('/')[0]
            vtysh_cmd += f" -c 'neighbor {ip} route-map M_{announce_net} out' "

            # announce /24 prefixes
            for part in range(num_routers):
                vtysh_cmd += f" -c 'network {announce_net}.10{str(part+1)}.0.0/24'"

            vtysh_cmd += f" -c 'exit' "
            os.popen(cmd.replace('X', vtysh_cmd))
            time.sleep(1)


def run_configs(announce_net: str, edges: dict, num_routers: int, minidir: str) -> None:
    '''
    announces from AS1 where to send which prefix to each arround AS (2 /24 prefixs per link)

    Arguments
    ---------
    announce_net (str): the identifier of the AS to announce the prefix's from
    edges (dict): dictionary that maps arround AS number to routers within center AS to routers in arround AS
    num_routers (int): number of routers within each AS
    minidir (str): path to mini internet directory
    '''
    for edge in edges:
        if edge != announce_net:
            connections: dict = edges[edge]
            routers_intern: list = connections.keys()

            used_prefixs: list = []  # lists all used prefixes to not reuse two

            for router_intern in routers_intern:
                routers_extern: list = connections[router_intern]

                for router_extern in routers_extern:
                    edge_cmd: str = "vtysh -c 'conf t' "
                    if router_extern not in HOLE_ROUTERS:
                        prefixs: list = []  # will include the numbers for prefixs to announce
                        # find prefixes to use on this connection:
                        for i in range(num_routers):
                            prefix: str = f'{announce_net}.10{str(i+1)}.0.0/24'
                            if prefix not in used_prefixs and len(prefixs) < 2:
                                used_prefixs.append(prefix)
                                prefixs.append(prefix)
                            if len(prefixs) == 2:
                                break

                        prefix_lists: list = []

                        # create prefix lists for selected prefixes
                        for prefix in prefixs:
                            edge_cmd += (f"-c 'ip prefix-list {announce_net}_"
                                         f"{prefixs.index(prefix) + len(used_prefixs)+1} seq 10 permit {prefix}' ")
                            prefix_lists.append(f'{announce_net}_{prefixs.index(prefix) + len(used_prefixs)+1}')

                        # create route-maps
                        for prefix_list in prefix_lists:
                            edge_cmd += (f" -c 'route-map M_{router_extern} permit {announce_net}0"
                                         f"{prefix_lists.index(prefix_list)}' ")
                            edge_cmd += f"  -c 'match ip address prefix-list {prefix_list}' "
                            edge_cmd += f"  -c 'set local-preference 5000000' "
                            edge_cmd += f"  -c 'exit' "

                        edge_cmd += f" -c 'router bgp 1' "

                        # get ip between from routers to center AS
                        ip: str = get_links(minidir).query((f'id1 == {edge} and id2 == 1 and router1 == '
                                                            f'"{router_extern}" and router2 == "{router_intern}"')
                                                           ).iloc[0]['ip'].split('/')[0]
                        edge_cmd += f" -c 'neighbor {ip} route-map M_{router_extern} out' "

                        for prefix in prefixs:
                            edge_cmd += f"  -c 'network {prefix}' "

                        edge_cmd += " -c 'exit' -c 'exit'"

                        os.popen(f'sudo docker exec -ti 1_{router_intern}router bash -c "{edge_cmd}"')
                        time.sleep(1)


def configure_balancing(num_routers: int, ases: list, edges: dict, minidir: str) -> None:
    '''
    configures the bgp policies such that only one link is used for a target IP when router has more than one link to
    same AS

    Arguments
    ---------
    num_routers (int): number of routers within each AS
    ases (list): list of identifying numbers for AS's in Mini-Internet
    edges (dict): dictionary that maps arround AS number to routers within center AS to routers in arround AS
    minidir (str): path to mini internet directory
    '''
    print('----- configure balancing -----')
    for i in ases:
        configure_external_AS(str(i), edges, num_routers, minidir)
    run_configs('1', edges, num_routers, minidir)
    for i in ases:
        run_configs(str(i), edges, num_routers, minidir)


def main() -> None:
    parser: argparse.ArgumentParser = init_parser()
    args: argparse.Namespace = parser.parse_args()

    minidir: str = args.dir

    num_routers, ases, edges = extract_infos(minidir)
    configure_balancing(num_routers, ases, edges, minidir)


if __name__ == '__main__':
    main()

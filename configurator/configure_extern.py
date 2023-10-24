#!/usr/bin/python3

import os
import time
import argparse
import pandas as pd

from config_helper import extract_infos, EGRESS_LINKS, CENTER_AS, get_links, get_routers_info

__author__ = 'Max Bergmann'


def init_parser() -> argparse.ArgumentParser:
    '''initializes a parser for the CLI'''
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir',
                        help='path to directory of mini internet',
                        type=str,
                        default='../mini-internet/platform',
                        )

    return parser


def configure_external_interfaces(num_ases: int, routers: list, minidir: str) -> None:
    '''
    this function configures the interfaces to external ASs/routers without connecting them

    Arguments
    ---------
    num_ases (int): number of AS's in Mini-Internet
    routers: names of routers within each AS
    minidir (str): path to mini internet directory
    '''
    print('----- configure external interfaces -----')

    for i in range(num_ases):
        group: int = i+1
        print(group)

        # setup interfaces to external routers
        for router in routers:
            ifaces = get_links(minidir).query(f'id1 == {str(group)} and router1 == "{router}"')
            if not ifaces.empty:
                cmd: str = f'vtysh -c \'conf t\' '
                for i in range(len(ifaces)):
                    connection = ifaces.iloc[i]
                    cmd += (f'-c \'interface ext_{connection.id2}_{connection.router2}\' '
                            f'-c \'ip address {connection.ip}\' '
                            f'-c \'exit\' ')
                os.popen(f'docker exec -d {str(group)}_{router}router bash -c "{cmd}"')
                time.sleep(1)


def configure_extern(num_ases: int, routers: list, minidir: str) -> None:
    '''
    this function will run the needed configuration commands to connect different ASs as peers and will create the
    needed route-maps for easy BGP policy change later (MAP_IN_{5, 50, 500, 5000, 50000})

    Arguments
    ---------
    num_ases (int): number of AS's in Mini-Internet
    routers: names of routers within each AS
    minidir (str): path to mini internet directory
    '''
    print('----- configure external connections -----')

    for i in range(num_ases):
        group: int = i+1
        print(group)

        maps: str = """ vtysh -c 'conf t' \
            -c 'bgp community-list 1 permit AS:10' \
            -c 'route-map MAP_IN_5 permit 10' \
            -c 'set community AS:10' \
            -c 'set local-preference 5' \
            -c 'exit' \
            -c 'route-map MAP_IN_50 permit 10' \
            -c 'set community AS:10' \
            -c 'set local-preference 50' \
            -c 'exit' \
            -c 'route-map MAP_IN_500 permit 10' \
            -c 'set community AS:10' \
            -c 'set local-preference 500' \
            -c 'exit' \
            -c 'route-map MAP_IN_5000 permit 10' \
            -c 'set community AS:10' \
            -c 'set local-preference 5000' \
            -c 'exit' \
            -c 'route-map MAP_IN_50000 permit 10' \
            -c 'set community AS:10' \
            -c 'set local-preference 50000' \
            -c 'exit' \
            -c 'route-map MAP_OUT permit 5' \
            -c 'match ip address prefix-list OWN_PREFIX' \
            -c 'exit' \
            -c 'route-map MAP_OUT permit 10' \
            -c 'match community 1' \
            -c 'exit' \
            -c 'exit'"""

        # setup route-maps and communities on all routers with external links
        for router in routers:
            ifaces = get_links(minidir).query(f'id1 == {str(group)} and router1 == "{router}"')
            if not ifaces.empty:
                r_cmd = maps.replace('AS', str(group))
                os.popen(f'docker exec -d {str(group)}_{router}router bash -c "{r_cmd}"')
                time.sleep(1)

        # setup bgp connection for first overall connectivity
        for router in routers:
            ifaces = get_links(minidir).query(f'id1 == {str(group)} and router1 == "{router}"')
            if not ifaces.empty:
                externals = []
                cmd: str = f'vtysh -c \'conf t\' -c \'router bgp {str(group)}\' '
                for i in range(len(ifaces)):
                    connection = ifaces.iloc[i]
                    if int(connection.ip.split('/')[0][-1]) == 1:
                        ip = connection.ip.split('/')[0][:-1] + '2'
                    else:
                        ip = connection.ip.split('/')[0][:-1] + '1'
                    cmd += f'-c \'neighbor {ip} remote-as {connection.id2}\' '
                    cmd += f'-c \'neighbor {ip} route-map MAP_IN_500 in\' '
                    cmd += f'-c \'neighbor {ip} route-map MAP_OUT out\' '
                    externals.append(connection.id2)

                cmd += f'-c \'network {str(group)}.0.0.0/8\' '  # announce own AS

                cmd += f'-c \'exit\' '
                cmd += f'-c \'exit\' -c \'write\''

                os.popen(f'docker exec -d {str(group)}_{router}router bash -c "{cmd}"')
                time.sleep(1)


def toggle_ipd(activate: bool, num_ases: int, minidir: str) -> None:
    '''
    deactivates connections between AS around center AS (default AS 1)

    Arguments
    ----------
    activate (bool): shutdowns links between around AS's if true, else reactivates them
    num_ases (int): number of AS's in Mini-Internet
    minidir (str): path to mini internet directory
    '''
    print('----- configure IPD Scenario -----')

    toogle_links: pd.DataFrame = get_links(minidir).query(f'id1!={str(CENTER_AS)}')

    for i in range(num_ases):
        group: int = i+1
        print(group)

        ifaces = toogle_links.query(f'id1 == {str(group)} and id2 != {str(CENTER_AS)}')
        if not ifaces.empty:
            for i in range(len(ifaces)):
                connection = ifaces.iloc[i]
                if int(connection.ip.split('/')[0][-1]) == 1:
                    ip = connection.ip.split('/')[0][:-1] + '2'
                else:
                    ip = connection.ip.split('/')[0][:-1] + '1'

                if activate:
                    shutdown_cmd: str = (f"vtysh -c 'conf t' -c 'router bgp {str(group)}' -c 'neighbor {ip} shutdown' "
                                         f"-c 'exit' -c 'exit'")
                else:
                    shutdown_cmd: str = (f"vtysh -c 'conf t' -c 'router bgp {str(group)}' -c 'no neighbor {ip}"
                                         f" shutdown' -c 'exit' -c 'exit'")
                cmd = f'sudo docker exec -d {str(group)}_{connection.router1}router bash -c "{shutdown_cmd}"'
                os.popen(cmd)
                time.sleep(1)


def define_egress_links(minidir: str) -> None:
    '''
    sets the one link from AS 1 to each other AS with higher preference and lower preference within the other AS's
    to AS 1. leads to one egress link to each AS for AS 1 --> use within IPD to potentially remove duplicate ingressing
    flows

    Arguments
    ----------
    minidir (str): path to mini internet directory
    '''
    print('----- define egress links in AS 1 -----')

    for link in EGRESS_LINKS:
        as1_r: str = link[0]
        extern_r: str = link[1]

        ip: str = get_links(minidir).query(
            f'id2 == 1 and router2 == "{as1_r}" and router1 == "{extern_r}"').iloc[0]['ip'].split('/')[0]

        # prefer specified link as egress link in AS 1
        vtysh_cmd: str = (f'vtysh -c \'conf t\' -c \'router bgp 1\' -c \'neighbor {ip} route-map MAP_IN_50000 in\' '
                          f'-c \'exit\' -c \'exit\' -c \'write\'')

        cmd: str = f'docker exec -d 1_{as1_r}router bash -c "{vtysh_cmd}"'
        os.popen(cmd)
        time.sleep(1)

        # prefer all other links against the egress link to AS 1
        connection: pd.DataFrame = get_links(minidir).query(
            f'id1 == 1 and router1 == "{as1_r}" and router2 == "{extern_r}"')
        ip: str = connection.iloc[0]['ip'].split('/')[0]
        target_net: int = connection.iloc[0]['id2']

        # unprefer specified link as egress link
        vtysh_cmd: str = (f'vtysh -c \'conf t\' -c \'router bgp {target_net}\' -c \'neighbor {ip} route-map MAP_IN_5 '
                          f'in\' -c \'exit\' -c \'exit\' -c \'write\'')

        cmd: str = f'docker exec -d {target_net}_{extern_r}router bash -c "{vtysh_cmd}"'
        os.popen(cmd)
        time.sleep(1)


def main() -> None:
    parser: argparse.ArgumentParser = init_parser()
    args: argparse.Namespace = parser.parse_args()

    minidir: str = args.dir

    _, ases, _ = extract_infos(minidir)

    configure_external_interfaces(len(ases)+1, get_routers_info(minidir)['name'].to_list(), minidir)
    configure_extern(len(ases)+1, get_routers_info(minidir)['name'].to_list(), minidir)
    toggle_ipd(True, len(ases)+1, minidir)
    define_egress_links(minidir)


if __name__ == '__main__':
    main()

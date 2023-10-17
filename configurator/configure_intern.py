#!/usr/bin/python3

import os
import time
import argparse
import pandas as pd

from config_helper import extract_infos, get_routers_info

__author__ = 'Max Bergmann'


def init_parser() -> argparse.ArgumentParser:
    '''initializes a parser for the CLI'''
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir',
                        help='path to directory of mini internet',
                        type=str,
                        default='/home/max/WORK/mini-internet/platform/',
                        )

    return parser


def configure_intern(num_ases: int, num_routers: int, routers: list, minidir: str) -> None:
    '''
    this function will run the needed configuration commands to enable full connectivity within one AS

    Arguments
    ---------
    num_ases (int): number of AS's used in Mini-Internet
    num_routers (int): number of routers per AS
    routers (list[str]): list of router names
    '''
    # information of IPs for linking the routers
    intern_config: pd.DataFrame = pd.read_csv(f'{minidir}/configurator/intern_config.csv')

    print('----- configure internal connections -----')
    for i in range(num_ases):
        group: int = i+1
        print(group)

        # configure routers
        for j in range(len(routers)):
            router: str = routers[j]

            cmd: str = (f'vtysh -c \'conf t\' '
                        f'-c \'dump bgp updates /home/bgpdump/updates/updates.5.%Y%m%d-%H%M 30m\' '
                        f'-c \'dump bgp routes-mrt /home/bgpdump/ribs/rib.5.%Y%m%d-%H%M 30m\' ')

            # add loopbackinterface in router
            cmd += (f'-c \'interface lo\' '
                    f'-c \'ip address {group}.15{str(j+1)}.0.1/24\' '
                    f'-c \'exit\' ')

            # add interfaces for hosts in router
            cmd += (f'-c \'interface host\' '
                    f'-c \'ip address {group}.10{str(j+1)}.0.2/24\' '
                    f'-c \'exit\' '
                    f'-c \'router ospf\' '
                    f'-c \'network {group}.10{str(j+1)}.0.2/24 area 0\' '
                    f'-c \'exit\' ')

            # define router ID
            cmd += (f'-c \'router ospf\' '
                    f'-c \'ospf router-id {group}.15{str(j+1)}.0.1\' '
                    f'-c \'network {group}.15{str(j+1)}.0.1/24 area 0\' '
                    f'-c \'exit\' ')

            cmd += (f'-c \'ip route {group}.0.0.0/8 null0\' '
                    f'-c \'ip prefix-list OWN_PREFIX seq 5 permit {group}.0.0.0/8\' '
                    f'-c \'route-map OWN_PREFIX permit 10\' '
                    f'-c \'match ip address prefix-list OWN_PREFIX\' '
                    f'-c \'exit\' ')

            # add internal BGP
            for k in range(num_routers):
                them: int = k+1
                if k+1 != j+1:
                    cmd += (f'-c \'router bgp {group}\' '
                            f'-c \'network {group}.0.0.0/8\' '
                            f'-c \'neighbor {group}.15{them}.0.1 remote-as {group}\' '
                            f'-c \'neighbor {group}.15{them}.0.1 update-source lo\' '
                            f'-c \'neighbor {group}.15{them}.0.1 next-hop-self\' '
                            f'-c \'address-family ipv6 unicast\' '
                            f'-c \'neighbor {group}.15{them}.0.1 activate\' '
                            f'-c \'exit\' '
                            f'-c \'exit\' ')

            i_links = intern_config.query(f'router == "{router}"')

            # define interfaces to other routers
            for j in range(len(i_links)):
                conf: pd.Series = i_links.iloc[j]

                cmd += (f'-c \'interface {conf.iface}\' '
                        f'-c \'ip address {conf.ip}\' '
                        f'-c \'ip ospf cost 1\' '
                        f'-c \'exit\' '
                        f'-c \'router ospf\' '
                        f'-c \'network {conf.ip} area 0\' '
                        f'-c \'exit\' ')

            cmd = cmd.replace(' x', f' {str(group)}')

            os.popen(f'docker exec -d {str(group)}_{router}router bash -c "{cmd}"')
            time.sleep(1)

        # add interface to router on host
        for j in range(len(routers)):
            router: str = routers[j]

            # set ip address for port to router
            cmd: str = (f'docker exec -d {str(group)}_{router}host bash -c "ip address add {group}.10{str(j+1)}.0'
                        f'.1/24 dev {router}router"')
            os.popen(cmd)
            time.sleep(1)

            # set the default gateway to router
            cmd: str = (f'docker exec -d {str(group)}_{router}host bash -c "ip route add default via '
                        f'{group}.10{str(j+1)}.0.2"')
            os.popen(cmd)
            time.sleep(1)


def main() -> None:
    parser: argparse.ArgumentParser = init_parser()
    args: argparse.Namespace = parser.parse_args()

    minidir: str = args.dir

    num_routers, ases, _ = extract_infos(minidir)
    configure_intern(len(ases)+1, num_routers, get_routers_info(minidir)['name'].to_list(), minidir)


if __name__ == '__main__':
    main()

#!/usr/bin/python3

import os
import argparse
import pandas as pd

from configure_intern import configure_intern
from configure_balancing import configure_balancing
from config_helper import extract_infos, get_routers_info
from configure_extern import configure_extern, toggle_ipd, define_egress_links, configure_external_interfaces

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


def main() -> None:
    '''
    configure the Mini-Internet for IPD usage including ingress link definition, prefix definition, internal
    configurations, balancing
    '''
    parser: argparse.ArgumentParser = init_parser()
    args: argparse.Namespace = parser.parse_args()

    minidir: str = args.dir
    routers_info: pd.DataFrame = get_routers_info(minidir)
    num_routers, ases, edges = extract_infos(minidir)

    configure_intern(len(ases)+1, num_routers, routers_info['name'].to_list(), minidir)
    configure_external_interfaces(len(ases)+1, routers_info['name'].to_list(), minidir)
    configure_extern(len(ases)+1, routers_info['name'].to_list(), minidir)
    toggle_ipd(True, len(ases)+1, minidir)
    define_egress_links(minidir)
    configure_balancing(num_routers, ases, edges, minidir)


if __name__ == '__main__':
    main()

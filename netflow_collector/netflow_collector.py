#!/usr/bin/python3

import os
import time
import argparse
import pandas as pd

from datetime import datetime, timedelta

__author__ = 'Max Bergmann'


def init_Parser() -> argparse.ArgumentParser:
    '''initializes the parser of this script with the needed arguments and returns the parser'''
    parser: argparse.ArgumentParser = argparse.ArgumentParser()

    parser.add_argument('-conda',
                        type=str,
                        help='path to miniconda environment',
                        )
    parser.add_argument('-ipd',
                        type=str,
                        help='path to the IPD directory',
                        default='../ipd-implementation/',
                        )
    parser.add_argument('-nf',
                        type=str,
                        help='path to shared directories that include router files and netflow',
                        default='../shared_directories/',
                        )
    parser.add_argument('-collector',
                        type=str,
                        help='path to netflow collector',
                        default='../netflow_collector/',
                        )
    parser.add_argument('-offset',
                        type=int,
                        help='minutes to jump back and collect netflow',
                        default=2,
                        )
    parser.add_argument('-i',
                        type=int,
                        help='time in seconds between each collection',
                        default=60,
                        )
    parser.add_argument('-v',
                        action='store_true',
                        help='verbose output set False if directly piped into IPD',
                        )

    return parser


def collect_netflow(args: argparse.Namespace, ingresses: pd.DataFrame) -> None:
    '''collects netflow from routers and starts preprocessing'''
    start: datetime = datetime.now() - timedelta(minutes=args.offset)
    
    netflow_path = args.ipd + '/netflow/mini/'
    netflow_dir = args.nf + '/router_files/netflow_mini-internet/'

    year: str = str(start.year)
    month: str = str(start.month) if start.month >= 10 else '0' + str(start.month)
    day: str = str(start.day) if start.day >= 10 else '0' + str(start.day)
    minute: str = str(start.minute) if start.minute >= 10 else '0' + str(start.minute)
    hour: str = str(start.hour) if start.hour >= 10 else '0' + str(start.hour)

    date: str = year + month + day + hour + minute

    dst_dir: str = netflow_path + date + '/'
    os.popen(f'mkdir -p {dst_dir}')

    for _, row in ingresses.iterrows():
        container: str = f'1_{row["PEER_SRC_IP"]}router'
        src_path: str = netflow_dir + f'AS_1/{container}/port-{row["IN_IFACE"]}/{year}/{month}/{day}/nfcapd.{date}'
        dst_name: str = f'1_{row["PEER_SRC_IP"]}_{row["IN_IFACE"]}_{year}{month}{day}{hour}{minute}'
        dst_path: str = dst_dir + f'nfcapd.{dst_name}'
        os.popen(f'mv {src_path} {dst_path}')
        os.popen(f'nfdump -r {dst_path} -o csv | gzip -9 > {dst_path}.csv.gz &')

    if args.v:
        os.system((f'bash {args.collector}/netflow_collector.sh '
                   f'{netflow_path} {date} {dst_dir} {args.conda} {args.collector} 1'))
    else:
        os.system((f'bash {args.collector}/netflow_collector.sh '
                   f'{netflow_path} {date} {dst_dir} {args.conda} {args.collector} 0'))


def main() -> None:
    starttime: datetime = time.monotonic()

    parser: argparse.ArgumentParser = init_Parser()
    args: argparse.Namespace = parser.parse_args()

    ingresses: pd.DataFrame = pd.read_csv(args.ipd + '/ingresslink/mini.txt')

    while True:
        # print(datetime.now())
        collect_netflow(args, ingresses)

        waiting = args.i - ((time.monotonic() - starttime) % args.i)
        time.sleep(waiting)


if __name__ == '__main__':
    main()

#!/usr/bin/python3

import time
import os
import pandas as pd

from datetime import datetime, timedelta

__author__ = 'Max Bergmann'


starttime: datetime = time.monotonic()
interval_time: int = 60

netflow_path: str = '../ipd-implementation/netflow/mini/'
connections_file: str = '../ipd-implementation/ingresslink/mini.txt'
netflow_dir: str = '../shared_directories/router_files/netflow_mini-internet/'
ingresses: pd.DataFrame = pd.read_csv(connections_file)

offset: int = 2  # minutes to jump back and collect netflow
netflow_offset: int = 1  # interval the netflow is generated


def collect_netflow() -> None:
    '''collects netflow from routers and starts preprocessing'''
    start: datetime = datetime.now() - timedelta(minutes=offset)

    year: str = str(start.year)
    month: str = str(start.month) if start.month >= 10 else '0' + str(start.month)
    day: str = str(start.day) if start.day >= 10 else '0' + str(start.day)
    minute: str = str(start.minute) if start.minute >= 10 else '0' + str(start.minute)
    hour: str = str(start.hour) if start.hour >= 10 else '0' + str(start.hour)

    date: str = year + month + day + hour + minute

    dst_dir: str = netflow_path + date + '/'
    os.popen(f'mkdir {dst_dir}')

    for _, row in ingresses.iterrows():
        container: str = f'1_{row["PEER_SRC_IP"]}router'
        src_path: str = netflow_dir + f'AS_1/{container}/port-{row["IN_IFACE"]}/{year}/{month}/{day}/nfcapd.{date}'
        dst_name: str = f'1_{row["PEER_SRC_IP"]}_{row["IN_IFACE"]}_{year}{month}{day}{hour}{minute}'
        dst_path: str = dst_dir + f'nfcapd.{dst_name}'
        os.popen(f'mv {src_path} {dst_path}')
        os.popen(f'nfdump -r {dst_path} -o csv | gzip -9 > {dst_path}.csv.gz &')

    os.system((f'bash netflow_collector.sh '
               f'{netflow_path} {date} {dst_dir}'))


def main() -> None:
    while True:
        print(datetime.now())
        collect_netflow()

        waiting = interval_time - ((time.monotonic() - starttime) % interval_time)
        time.sleep(waiting)


if __name__ == '__main__':
    main()

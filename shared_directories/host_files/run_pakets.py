#!/usr/bin/python3

import time
import random
import argparse
import numpy as np
import pandas as pd

from scapy.all import IP, send, UDP
from datetime import datetime, timedelta

__author__ = 'Max Bergmann'

random.seed(2212976604)  # add a seed for pseudo randomness


def init_parser() -> argparse.ArgumentParser:
    '''initializes a parser for the CLI'''
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-a',
        default=1,
        type=int,
        help='the id of network to start scapy processes in',
    )
    parser.add_argument(
        '-i',
        default=0,
        type=int,
        help='the iteration (hour) within a daily cirle (optional)',
    )
    parser.add_argument(
        '-t',
        default=60.0,
        type=float,
        help='the time in seconds that represents one iteration/hour',
    )
    parser.add_argument(
        '-r',
        default=1,
        type=int,
        help='the id of router within network to start scapy processes in',
    )
    parser.add_argument(
        '-n',
        default=0.0,
        type=float,
        help='portion of noise to generate (between 0 and 1)',
    )
    parser.add_argument(
        '-o',
        action='store_true',
        default=False,
        help='indicates overflow event',
    )
    parser.add_argument(
        '-v',
        action='store_true',
        default=False,
        help='output the proceedings',
    )
    parser.add_argument(
        '-dir',
        default='/home/host_files/',
        type=str,
        help='path to mounted directory in container',
    )

    return parser


def run_pakets(
        iteration: int,
        interval_time: float,
        net: int,
        router: int,
        dir: str,
        verbose: bool = False,
        noise: float = 0.0,
        overflow: bool = False) -> None:
    '''
    will infinitely send configured pakets for one router within an AS within one minute. Additionally can generate
    noise traffic and start offloaded traffic

    Arguments
    ---------
    iteration (int): will be the iteration of daily simulation (0 in general for normal usage)
    net (int): AS the traffic originates
    router (int): identification number of router in AS
    verbose (bool): set True to get debug output
    noise (float): part of traffic that gets noisy
    overflow (bool): set True if this AS is included in an overflow event
    '''
    # includes the src AS number and the target IP of packages
    if overflow:
        if verbose:
            print('Start offloaded traffic')
        combinations: pd.DataFrame = pd.read_csv(f'{dir}/connections_{str(net)}_overflow.csv')
    else:
        combinations: pd.DataFrame = pd.read_csv(f'{dir}/connections_{str(net)}.csv')
    combinations.query(f'router == {str(router)} and iteration == {iteration}', inplace=True)

    pakets: list = []
    for i in range(len(combinations)):
        paket = combinations.iloc[i]
        pakets.append(IP(src=paket.sip, dst=paket.dip)/UDP(sport=paket.sport, dport=paket.dport))

    # add portional noise to pakets by changing the src address randomly
    part_noise = random.sample(range(0, len(pakets)), int(round(noise * len(pakets), 0)))
    noise_nets: list = [x for x in np.arange(1, 6, 1) if x != net]
    for i in part_noise:
        # select for this connection the fake source AS without selecting the same AS as the target
        ran_net = random.choice([x for x in noise_nets if x != pakets[i].dst.split('.')[0]])
        ran_router = random.choice(np.arange(101, 109, 1))
        ran_host = random.choice(np.arange(1, 100, 1))
        change_ip = f'{ran_net}.{ran_router}.0.{ran_host}'
        pakets[i].src = change_ip

    if verbose:
        print(f'Any duplicated pakets? -> {combinations.duplicated().any()}')
        print(f'send {len(pakets)} pakets every {interval_time} seconds:')

    counter: int = 0
    bunch_size: int = 900

    # pakets = pakets[:900]

    starttime = time.monotonic()
    # transmit packages distributed over 1 minute to reduce CPU usage
    while True:
        sended: int = 0  # will count the sended pakets per iteration
        start: datetime = datetime.now()
        b_counter: int = 0  # counter how many bunches where already send

        if verbose:
            print(f'\t|------------------------------------')
            print(f'\t| {counter}:\t{start}')

        last_index: int = 0  # index of last send pakets

        while last_index < len(pakets):
            if last_index+bunch_size >= len(pakets):  # send last pakets
                send(pakets[last_index:], verbose=0)
                sended += len(pakets[last_index:])
                if verbose:
                    print(f'\t| send:\t{len(pakets[last_index:])}')
            else:  # send bunch of pakets
                send(pakets[last_index:last_index+bunch_size], verbose=0)
                sended += len(pakets[last_index:last_index+bunch_size])

                # calculate waiting time to execute within 10 seconds
                # waiting = interval_time*(b_counter+1)-((time.monotonic()-starttime) % interval_time*(b_counter+1))
                waiting = 1*(b_counter+1)-((time.monotonic()-starttime) % 1*(b_counter+1))
                b_counter += 1
                time.sleep(waiting)

                if verbose:
                    print(f'\t| send:\t{len(pakets[last_index:last_index+bunch_size])}')
            last_index = last_index+bunch_size

        counter += 1

        # calculate execution time and waiting time to execute next iteration after 1 minute
        end: datetime = datetime.now()
        if verbose:
            print(f'\t| exec:\t{end-start}')
            print(f'\t| send:\t{sended} pakets')
            print(f'\t| {counter}:\t{end}')

        for i in part_noise:
            # select for this connection the fake source AS without selecting the same AS as the target
            ran_net = random.choice([x for x in noise_nets if x != pakets[i].dst.split('.')[0]])
            ran_router = random.choice(np.arange(101, 109, 1))
            ran_host = random.choice(np.arange(1, 100, 1))
            change_ip = f'{ran_net}.{ran_router}.0.{ran_host}'
            pakets[i].src = change_ip

        # calculate waiting time to send all packages within the given interval_time
        waiting = interval_time - ((time.monotonic() - starttime) % interval_time)

        if verbose:
            print(f'\t| wait:\t{waiting} seconds')
            print(f'\t|------------------------------------\n')

        time.sleep(waiting)


def main() -> None:
    parser: argparse.ArgumentParser = init_parser()
    args: argparse.Namespace = parser.parse_args()

    net: int = args.a  # one of 2 - 5
    router: int = args.r  # one of 1 - 8
    verbose: bool = args.v
    noise: float = args.n  # portion of noise to generate
    overflow: bool = args.o  # indicates if an overflow event was triggered
    dir: str = args.dir  # path to mounted directory

    run_pakets(args.i, args.t, net, router, dir, verbose, noise, overflow)


if __name__ == '__main__':
    main()

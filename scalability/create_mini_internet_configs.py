#!/usr/bin/python3
import sys

__author__ = 'Max Bergmann'

ASES: int = int(sys.argv[1])

AS_CONFIG_FILE: str = '../mini-internet/platform/config/AS_config.txt'
EXTERNAL_LINKS_CONFIG_FILE: str = '../mini-internet/platform/config/external_links_config.txt'

CENTER_AS: int = 1
ROUTERS: list = ['LOND', 'BARC', 'COTT', 'SAOP', 'NEWY', 'SANF', 'MIAM', 'ACCR']
OFFSET: int = 4
ARROUND: int = 5

CONNECTIONS: dict = {
    2: [
        ('LOND', 'BARC'),
        ('BARC', 'MIAM'),
        ('COTT', 'BARC'),
        ('COTT', 'NEWY'),
        ('COTT', 'MIAM'),
    ],
    3: [
        ('LOND', 'MIAM'),
        ('NEWY', 'BARC'),
        ('NEWY', 'NEWY'),
        ('NEWY', 'MIAM'),
        ('SANF', 'BARC'),
    ],
    4: [
        ('NEWY', 'COTT'),
        ('SANF', 'COTT'),
        ('SANF', 'SANF'),
        ('SANF', 'LOND'),
        ('MIAM', 'LOND'),
    ],
    5: [
        ('MIAM', 'COTT'),
        ('ACCR', 'LOND'),
        ('SAOP', 'COTT'),
        ('SAOP', 'SANF'),
        ('SAOP', 'LOND'),
    ]
}


def write_as_config():
    '''creates the config file that initializes the number of ASes in Mini-Internet'''
    with open(AS_CONFIG_FILE, 'w') as file:
        for i in range(1, ASES+1, 1):
            line: str = (f'{i} AS NoConfig router_config_full.txt internal_links_config_full.txt '
                         f'layer2_switches_config.txt layer2_hosts_config.txt layer2_links_config.txt\n')
            file.writelines(line)


def write_external_configs():
    '''creates the configs for connections between ASes'''
    ip_counter: int = 1

    round: int = 0
    counter: int = 1

    ip_offset: int = 0

    with open(EXTERNAL_LINKS_CONFIG_FILE, 'w') as file:
        for i in range(2, ASES+1, 1):
            target_as: int = i - (round*OFFSET)
            # print(f'{i}: {i - (round*offset)}')
            cons: list = CONNECTIONS[target_as]

            for con in cons:
                file.write(f'1 {con[0]} Peer {i} {con[1]} Peer 100000 1000 179.0.{ip_counter}.{1+ip_offset}/24\n')
                file.write(f'{i} {con[1]} Peer 1 {con[0]} Peer 100000 1000 179.0.{ip_counter}.{2+ip_offset}/24\n')
                ip_counter += 1
                if ip_counter == 256:
                    ip_counter = 1
                    ip_offset += 2

            counter += 1
            if counter == ARROUND:
                round += 1
                counter = 1


if __name__ == '__main__':
    write_as_config()
    write_external_configs()

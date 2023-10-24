import sys
import time
import random
import pandas as pd
import numpy as np
from netaddr import IPNetwork
from scapy.all import IP, send, UDP, TCP, Ether


random.seed(2212976604)
# src = sys.argv[1]


ips = IPNetwork(f'2.101.0.0/24')
list_ips = list(ips)[1:-1]
list_ips = [str(x.ipv4()) for x in list_ips if str(x.ipv4()) != '2.101.0.2']

ips = IPNetwork(f'4.103.0.0/24')
list_ips_2 = list(ips)[1:-1]
list_ips_2 = [str(x.ipv4()) for x in list_ips_2]

ports: list = np.arange(20000, 65535, 1).tolist()

pakets = []
connections = []

# print(list_ips)

for _ in range(100):
    sport = random.choice(ports)
    ports.remove(sport)
    dport = random.choice(ports)
    ports.remove(dport)
    ip1 = random.choice(list_ips)
    # ip1 = '2.101.0.6'
    ip2 = random.choice(list_ips_2)
    # ip2 = '4.103.0.1'
    paket = IP(src=ip1, dst=ip2)/UDP(sport=sport, dport=dport)
    # paket = IP(src=ip1, dst=ip2)/UDP(sport=sport, dport=dport)
    pakets.append(paket)
    connections.append([ip1, sport, ip2, dport])

# send(pakets, verbose=True)
send(pakets, verbose=True)
# time.sleep(1)
# send(pakets[105:200], verbose=True)
# time.sleep(1)
# send(pakets[200:], verbose=True)

# pakets = []
# time.sleep(10)

# for _ in range(300):
#     sport = random.choice(ports)
#     ports.remove(sport)
#     dport = random.choice(ports)
#     ports.remove(dport)
#     ip1 = random.choice(list_ips)
#     # ip1 = '2.101.0.6'
#     ip2 = random.choice(list_ips)
#     ip2 = '4.101.0.1'
#     paket = IP(src=ip1, dst=ip2)/UDP(sport=sport, dport=dport)
#     # paket = IP(src=ip1, dst=ip2)/UDP(sport=sport, dport=dport)
#     pakets.append(paket)
#     connections.append([ip1, sport, ip2, dport])

# send(pakets, verbose=True)

# pakets = []
# time.sleep(10)

# for _ in range(100):
#     sport = random.choice(ports)
#     ports.remove(sport)
#     dport = random.choice(ports)
#     ports.remove(dport)
#     ip1 = random.choice(list_ips)
#     # ip1 = '2.101.0.6'
#     ip2 = random.choice(list_ips)
#     ip2 = '4.101.0.1'
#     paket = IP(src=ip1, dst=ip2)/UDP(sport=sport, dport=dport)
#     # paket = IP(src=ip1, dst=ip2)/UDP(sport=sport, dport=dport)
#     pakets.append(paket)
#     connections.append([ip1, sport, ip2, dport])

# send(pakets, verbose=True)

# df = pd.DataFrame(connections)
# print(df.duplicated().any())
# df.to_csv('host_files/pakets.csv', header=None, index=False)
# while True:
# paket = IP(src='2.104.0.1', dst=random.choice(list_ips))/UDP(sport=random.choice(ports),
# dport=random.choice(ports))
# paket = IP(src=random.choice(list_ips), dst='4.104.0.1')/UDP(sport=15000, dport=15000)
# paket = IP(src=random.choice(list_ips), dst=random.choice(list_ips_2))/UDP(sport=15000,
                                                                        #    dport=15000)

# paket = IP(src=random.choice(list_ips), dst='4.104.0.1')/TCP(sport=random.choice(ports),
# dport=random.choice(ports))
# send(pakets, verbose=True)
# time.sleep(1)

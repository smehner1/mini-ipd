#!/bin/bash
ROUTERNAME=$1
NETFLOW_DIR=$2
NETFLOW_ROTATE_INTERVAL=$3
NETFLOW_SAMPLING=$4
AS=$5

# Base port
PORT_NUM=2000

# Start the fprobe netflow collector on every interface but
# lo (netflow traffic)
# ssh (student activity)
# TODO: only start nfcapd on ingressing interfaces to reduce load
INTERFACES=$(ls /sys/class/net/ | grep -v lo | grep -v ssh)
for iface in $INTERFACES; do

    # One netflow dir per interface since fprobe sadly doesn't log
    # SNMP interface ID's. This also carries the human-readable
    # interface names over to the directory names.
    # if [ ! -d $NETFLOW_DIR ]; then
    #     mkdir -p $NETFLOW_DIR
    # fi
    # if [ ! -d "${NETFLOW_DIR}/AS_${AS}" ]; then
    #     mkdir -p "${NETFLOW_DIR}/AS_${AS}"
    # fi
    if [ ! -d "${NETFLOW_DIR}/AS_${AS}/${ROUTERNAME}" ]; then
        mkdir -p "${NETFLOW_DIR}/AS_${AS}/${ROUTERNAME}"
    fi

    OUTDIR="${NETFLOW_DIR}/AS_${AS}/${ROUTERNAME}/port-${iface}"

    if [ ! -d $OUTDIR ]; then
        mkdir -p $OUTDIR
    fi

    ifconfig $iface > $OUTDIR/ifconfig.txt

    # Start netflow capture to collect netflow sent by the fprobes
    # nfcapd -T +1,+4,+5,+10,+11,+13 -p ${PORT_NUM} -I "${ROUTERNAME}-port-${iface}" -l $OUTDIR -s $NETFLOW_SAMPLING -S 1 -D -t $NETFLOW_ROTATE_INTERVAL -P /var/run/nfcapd-$PORT_NUM.pid
    # nfcapd -T +1,+4,+5,+10,+11,+13 -p ${PORT_NUM} -I "${ROUTERNAME}-port-${iface}" -l $OUTDIR -s 1 -S 1 -D -t $NETFLOW_ROTATE_INTERVAL -P /var/run/nfcapd-$PORT_NUM.pid
    nfcapd -T +1,+4,+5,+10,+11,+13 -p ${PORT_NUM} -I "${ROUTERNAME}-port-${iface}" -l $OUTDIR -s 1 -S 1 -D -t 15 -P /var/run/nfcapd-$PORT_NUM.pid

    # fprobe cannot even mark the packet direction (in/out)
    # fix: filter by interface mac and tag with -x
    iface_mac=$(cat /sys/class/net/$iface/address)
    # fprobe -i $iface -e 30 -d 10 -g 10 -q 900 -s 1 localhost:$PORT_NUM
    fprobe -i $iface -f "not icmp" -e 30 -d 10 -g 10 -q 900 -s 1 localhost:$PORT_NUM

    PORT_NUM=$((PORT_NUM+1))
done

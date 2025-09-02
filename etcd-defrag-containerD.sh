#!/bin/bash

set -euo pipefail

export CRI_CONFIG_FILE="/var/lib/rancher/rke2/agent/etc/crictl.yaml"
CERT="/var/lib/rancher/rke2/server/tls/etcd/server-client.crt"
KEY="/var/lib/rancher/rke2/server/tls/etcd/server-client.key"
CA="/var/lib/rancher/rke2/server/tls/etcd/server-ca.crt"
CRICTL="/var/lib/rancher/rke2/bin/crictl"

echo "Locating etcd container..."
etcdcontainer=$(chroot /host $CRICTL ps --label io.kubernetes.container.name=etcd --quiet)

if [ -z "$etcdcontainer" ]; then
    echo "ERROR: etcd container not found!"
    exit 1
fi

echo "ETCD Member List:"
chroot /host $CRICTL exec $etcdcontainer etcdctl \
  --cert $CERT --key $KEY --cacert $CA \
  member list

echo "Cluster Endpoint Status (before clean):"
chroot /host $CRICTL exec $etcdcontainer etcdctl \
  --cert $CERT --key $KEY --cacert $CA \
  endpoint status --cluster --write-out=table

echo "Obtaining current revision..."
rev=$(chroot /host $CRICTL exec $etcdcontainer etcdctl \
  --cert $CERT --key $KEY --cacert $CA \
  endpoint status --write-out fields | grep Revision | head -n1 | awk '{print $2}')

echo "Compacting etcd at revision $rev ..."
chroot /host $CRICTL exec $etcdcontainer etcdctl \
  --cert $CERT --key $KEY --cacert $CA \
  compact $rev

echo "Defragmenting etcd cluster ..."
chroot /host $CRICTL exec $etcdcontainer etcdctl \
  --cert $CERT --key $KEY --cacert $CA \
  defrag --cluster

echo "Cluster Endpoint Status (after clean):"
chroot /host $CRICTL exec $etcdcontainer etcdctl \
  --cert $CERT --key $KEY --cacert $CA \
  endpoint status --cluster --write-out=table

echo "ETCD cleanup and defragmentation complete for RKE2 with containerD."

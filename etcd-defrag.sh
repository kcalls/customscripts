#!/bin/bash

cluster=$1

# Extract etcd node information (assuming it's available)
etcd_node=$(kubectl get nodes -l node-role.kubernetes.io/etcd=true -o jsonpath='{.items[0].metadata.name}' --context=$cluster)

# Create debug container on etcd node
kubectl debug node/$etcd_node -it --image=<your-artifactory-image> --context=$cluster -- /bin/bash <<EOF
  # Change root to /host
  chroot /host
  
  # Execute etcd commands
  docker exec etcd etcdctl member list
  docker exec -e ETCDCTL_ENDPOINTS=$(docker exec etcd etcdctl member list | cut -d, -f5 | sed -e 's/ //g' | paste -sd ',') etcd etcdctl endpoint status --write-out table
  docker exec -e ETCDCTL_ENDPOINTS=$(docker exec etcd etcdctl member list | cut -d, -f5 | sed -e 's/ //g' | paste -sd ',') etcd etcdctl endpoint health
  rev=$(docker exec etcd etcdctl endpoint status --write-out json | egrep -o '"revision":[0-9]*' | egrep -o '[0-9]*')
  docker exec etcd etcdctl compact "$rev"
  docker exec -e ETCDCTL_ENDPOINTS=$(docker exec etcd etcdctl member list | cut -d, -f5 | sed -e 's/ //g' | paste -sd ',') etcd etcdctl defrag --command-timeout=60s
  docker exec -e ETCDCTL_ENDPOINTS=$(docker exec etcd etcdctl member list | cut -d, -f5 | sed -e 's/ //g' | paste -sd ',') etcd etcdctl endpoint status --write-out table
EOF

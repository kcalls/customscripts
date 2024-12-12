#!/bin/bash

# Fetch the pod memory usage, requests, and limits
kubectl top pods --all-namespaces | while read line; do
    if [[ "$line" =~ ^NAMESPACE ]]; then
        echo -e "$line\t%MEM/R\t%MEM/L"
    else
        namespace=$(echo $line | awk '{print $1}')
        pod=$(echo $line | awk '{print $2}')
        mem_usage=$(echo $line | awk '{print $4}' | sed 's/Mi//')

        # Get resource requests and limits from pod spec
        resources=$(kubectl get pod $pod -n $namespace -o jsonpath='{.spec.containers[*].resources}')
        mem_request=$(echo $resources | jq -r '.requests.memory' | sed 's/Mi//')
        mem_limit=$(echo $resources | jq -r '.limits.memory' | sed 's/Mi//')

        # Calculate %MEM/R and %MEM/L if values exist
        if [[ -n $mem_request && -n $mem_limit ]]; then
            mem_request_percent=$((100 * mem_usage / mem_request))
            mem_limit_percent=$((100 * mem_usage / mem_limit))
        else
            mem_request_percent="N/A"
            mem_limit_percent="N/A"
        fi

        echo -e "$line\t$mem_request_percent%\t$mem_limit_percent%"
    fi
done

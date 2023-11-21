#!/bin/bash

age=${1:-60} # how many days to keep logs
shift
state_age=${1:-60} # how many days to keep state

dirs="/var/log/gwms-factory/client /var/log/gwms-factory/server"
state_dir="/var/lib/gwms-factory/web-area/stage"

for d in $dirs; do
  find $d -type f -mtime +${age} | xargs rm -f
done

find $state_dir -type f -mtime +${state_age} | xargs rm -f

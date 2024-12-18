#!/bin/bash

age=${1:-60} # how many days to keep logs
shift
state_age=${1:-60} # how many days to keep state

dirs="/var/log/gwms-factory/client /var/log/gwms-factory/server"
state_dir="/var/lib/gwms-factory/web-area/stage"

for d in $dirs; do
  find $d -type f -mtime +${age} | xargs rm -f
done

num_desc=$(ls ${state_dir}/description.* | wc -l)
to_remove=$(find $state_dir -maxdepth 1 -name 'description.*' -mtime +${state_age} | wc -l)

# make sure we keep at least one reconfig around
if [ $to_remove -gt 0 -a $to_remove -lt $num_desc ];then
  find $state_dir -type f -mtime +${state_age} | xargs rm -f
fi

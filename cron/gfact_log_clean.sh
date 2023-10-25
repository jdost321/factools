#!/bin/bash

age=$1 # how many days to keep logs

dirs="/var/log/gwms-factory/client /var/log/gwms-factory/server /var/lib/gwms-factory/web-area/stage"

for d in $dirs; do
  find $d -type f -mtime +${age} | xargs rm -f
done

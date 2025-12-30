#!/bin/bash

script_dir=`dirname $0`
conf=${script_dir}/../etc/rsync_clientlogs.conf
pidfile=${script_dir}/../var/lock/rsync_clientlogs.pid

if [ -e $pidfile ]; then
    pid=$(cat $pidfile)
    if kill -0 $pid >/dev/null 2>&1; then
        exit 0
    fi
fi
echo $$ >$pidfile

extra_args=""

while read line; do
  if [ -n "$line" ] && ! echo "$line" | grep -q '^#'; then
    set -- $line
    user=$1
    shift
    src=$1
    shift
    dest=$1
    shift
    if [ $# -gt 0 ]; then
      if [ $1 = "--delete" ]; then
        extra_args=$1
      fi
    fi

    timeout 1h /usr/bin/rsync -e "ssh -o StrictHostKeyChecking=no -i /home/${user}/.ssh/id_rsa" --timeout 2700 --include "/entry_*/" --include "/entry_*/job.*.out" --include "/entry_*/job.*.err" --exclude "*" --min-size 1 -axv --chmod=+r $extra_args $src $dest >/tmp/rsync_${user}.log 2>&1
  fi
done < $conf

rm $pidfile

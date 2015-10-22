#!/bin/bash

script_dir=`dirname $0`
conf=${script_dir}/../etc/rsync_clientlogs.conf
lock=${script_dir}/../var/lock/rsync_clientlogs.lock

[ -e $lock ] && exit 0

touch $lock

while read line; do
  if [ -n "$line" ] && ! echo "$line" | grep -q '^#'; then
    set -- $line
    user=$1
    shift
    src=$1
    shift
    dest=$1
    shift

    su $user -c "/usr/bin/rsync -e 'ssh -c blowfish' --include '/entry_*/' --include '/entry_*/job.*.out' --include '/entry_*/job.*.err' --exclude '*' --min-size 1 -axv $src $dest >/tmp/rsync_${user}.log"
  fi
done < $conf

rm $lock

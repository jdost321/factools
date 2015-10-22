#!/bin/bash

script_dir=`dirname $0`
ft_env=${script_dir}/../etc/factools-env.sh
if [ -e $ft_env ];then
    . $ft_env
fi

if [ -n "$GLIDEIN_FACTORY_DIR" ];then
  factory_dir=$GLIDEIN_FACTORY_DIR
else
  factory_dir=/var/lib/gwms-factory/work-dir
fi

[ -e /etc/profile.d/condor.sh ] && . /etc/profile.d/condor.sh
now=`date +%s`
age=30
sleep=1200

if [ "$#" -ge 1 ];then
  age=$1
fi

pushd $factory_dir > /dev/null
schedds=`head -n 1 glideinWMS.xml | sed 's/^.*schedd_name="\([^"]\+\)".*/\1/' | tr , ' '`
popd > /dev/null

for schedd in $schedds;do
    condor_rm -name $schedd -const "qdate <= $((now - 3600*24*age))"
done

sleep $sleep

for schedd in $schedds;do
    condor_rm -forcex -name $schedd -const "qdate <= $((now - 3600*24*age))"
    # if there are any X left that have been X for > 1h just remove them
    condor_rm -forcex -name $schedd -const 'jobstatus==3 && (currenttime-enteredcurrentstatus>3600)'
done

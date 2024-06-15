#!/bin/bash

script_dir=`dirname $0`
ft_env=${script_dir}/../etc/factools-env.sh
if [ -e $ft_env ];then
    . $ft_env
fi

# try k8s config location first
conf=/etc/gwms-factory/config.d/01-glidein-instance.xml

# if not found try top level gwms config
if [ ! -e $conf ];then
    conf=/etc/gwms-factory/glideinWMS.xml

    if [ ! -e $conf ];then
        echo "ERROR neither /etc/gwms-factory/config.d/01-glidein-instance.xml nor /etc/gwms-factory/glideinWMS.xml found; exiting" >&2
        exit 1
    fi
fi

[ -e /etc/profile.d/condor.sh ] && . /etc/profile.d/condor.sh
now=`date +%s`
age=30
sleep=1200

if [ "$#" -ge 1 ];then
  age=$1
fi

schedds=`head -n 1 $conf | sed 's/^.*schedd_name="\([^"]\+\)".*/\1/' | tr , ' '`

for schedd in $schedds;do
    condor_rm -name $schedd -const "qdate <= $((now - 3600*24*age))"
done

sleep $sleep

for schedd in $schedds;do
    condor_rm -forcex -name $schedd -const "qdate <= $((now - 3600*24*age))"
    # if there are any X left that have been X for > 1h just remove them
    condor_rm -forcex -name $schedd -const 'jobstatus==3 && (currenttime-enteredcurrentstatus>3600)'
done

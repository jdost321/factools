#!/bin/bash

source ~/.bash_profile
source  /etc/profile.d/condor.sh
now=`date +%s`
age=$1
sleep=1200

pushd $GLIDEIN_FACTORY_DIR > /dev/null
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

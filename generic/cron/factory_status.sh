#!/bin/bash

script_dir=`dirname $0`
ft_env=${script_dir}/../../etc/factools-env.sh
if [ -e $ft_env ];then
    . $ft_env
fi

# Fail if factory dir is not set
if [ -z "$GLIDEIN_FACTORY_DIR" ]; then
    exit 1
fi
if [ -n "GLIDEIN_FACTORY_NAME" ];then
    factory_name="$GLIDEIN_FACTORY_NAME "
fi

cd $GLIDEIN_FACTORY_DIR
STATUS=`./factory_startup status`
DESIRED="Running"
RETEST="10m"
EMAIL=$1




if [ "$STATUS" != "$DESIRED" ]; then
    sleep $RETEST
    STATUS=`./factory_startup status`
    if [ "$STATUS" != "$DESIRED" ]; then
	DATE="on `date +%D` at `date +%T`"
	echo -e "WARNING: ${factory_name}Glidein Factory is not running.\nStatus: $STATUS\nLocation: $GLIDEIN_FACTORY_DIR\nPlease investigate.\n$DATE" | mail -s "WARNING: ${factory_name}Glidein Factory not running" $EMAIL
    fi
fi


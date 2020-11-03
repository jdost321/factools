#!/bin/bash

script_dir=`dirname $0`
ft_env=${script_dir}/../etc/factools-env.sh
if [ -e $ft_env ];then
    . $ft_env
fi

# default to rpm way
stat_cmd="/bin/systemctl status gwms-factory.service"

# if set, assume non rpm-install
if [ -n "$GLIDEIN_FACTORY_DIR" ]; then
    stat_cmd="${GLIDEIN_FACTORY_DIR}/factory_startup status"
fi
if [ -n "$GLIDEIN_FACTORY_NAME" ];then
    factory_name="$GLIDEIN_FACTORY_NAME "
fi

$stat_cmd | grep "active (running)"
STATUS=$?
DESIRED=0
RETEST="10m"
EMAIL=$1




if [ "$STATUS" != "$DESIRED" ]; then
    sleep $RETEST
    $stat_cmd | grep "active (running)"
    STATUS=$?
    if [ "$STATUS" != "$DESIRED" ]; then
	DATE="on `date +%D` at `date +%T`"
	echo -e "WARNING: ${factory_name}Glidein Factory is not running.\nLocation: $GLIDEIN_FACTORY_DIR\nPlease investigate.\n$DATE" | mail -s "WARNING: ${factory_name}Glidein Factory not running" $EMAIL
    fi
fi


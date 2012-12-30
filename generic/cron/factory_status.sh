#!/bin/bash
source ~/.bash_profile
cd $GLIDEIN_FACTORY_DIR
if [ -n "GLIDEIN_FACTORY_NAME" ];then
    factory_name="$GLIDEIN_FACTORY_NAME "
fi

STATUS=`./factory_startup status`
DESIRED="Running"
RETEST="10m"
EMAIL=$1




if [ "$STATUS" != "$DESIRED" ]; then
    sleep $RETEST
    STATUS=`./factory_startup status`
    if [ "$STATUS" != "$DESIRED" ]; then
	DATE="on `date +%D` at `date +%T`"
	echo -e "WARNING: ${factory_name}Glidein Factory is not running.\nStatus: $STATUS\nLocation: $FACTORY_DIR\nPlease investigate.\n$DATE" | mail -s "WARNING: ${factory_name}Glidein Factory not running" $EMAIL
    fi
fi


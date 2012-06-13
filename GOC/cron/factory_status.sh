#!/bin/bash
source ~/.bash_profile
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
	echo -e "WARNING: GOC Glidein Factory is not running.\nStatus: $STATUS\nLocation: $FACTORY_DIR\nPlease investigate.\n$DATE" | mail -s "WARNING: GOC Glidein Factory not running" $EMAIL
    fi
fi


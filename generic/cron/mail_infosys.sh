#!/bin/bash

script_dir=`dirname $0`
ft_env=${script_dir}/../../etc/factools-env.sh
if [ -e $ft_env ];then
    . $ft_env
fi

# Fail if reply-to is not set
if [ -z "$GLIDEIN_MAIL_REPLY_TO" ]; then
    exit 1
fi
# Fail if factory dir is not set
if [ -z "$GLIDEIN_FACTORY_DIR" ]; then
    exit 1
fi
if [ -n "GLIDEIN_FACTORY_NAME" ];then
    factory_name="$GLIDEIN_FACTORY_NAME "
fi

emails=$1
subject="${factory_name}Infosys Report `date +%m-%d-%Y`"
conf=${GLIDEIN_FACTORY_DIR}/glideinWMS.xml
body=`${script_dir}/../libexec/check_infosys.py $conf`

#echo "$body"
/usr/sbin/sendmail -oi -t <<EOF
To: ${emails}
Reply-to: ${GLIDEIN_MAIL_REPLY_TO}
Subject: ${subject}
Content-Type: text/html; charset=us-ascii
Content-Transfer-Encoding: 7bit
MIME-Version: 1.0

<pre>
$body
</pre>

EOF

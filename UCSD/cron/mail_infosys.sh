#!/bin/bash

# Fail if reply-to is not set
if [ -z "$GLIDEIN_MAIL_REPLY_TO" ]; then
    exit 1
fi

emails=$1
subject="Infosys Report `date +%m-%d-%Y`"
conf=/home/gfactory/glideinsubmit/glidein_Production_v4_3/glideinWMS.xml
script_dir=`dirname $0`
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

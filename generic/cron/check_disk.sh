#!/bin/bash

source ~/.bash_profile

# Fail if reply-to is not set
if [ -z "$GLIDEIN_MAIL_REPLY_TO" ]; then
    exit 1
fi

if [ -n "GLIDEIN_FACTORY_NAME" ];then
    factory_name="$GLIDEIN_FACTORY_NAME "
fi

emails=$1

subject="${factory_name}Factory Disk Warning `date +%m-%d-%Y`"
limit=${2:-80}

out=`df -h`

hit=false
for s in `echo "$out" | grep '[0-9]%' | sed 's|.* \([0-9]\+\)%.*|\1|g'`;do if [ $s -ge $limit ]; then hit=true;fi;done

if ! $hit; then
    exit 0
fi

body=`echo -e "WARNING Partition ${limit}% full!\n\n${out}"`

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


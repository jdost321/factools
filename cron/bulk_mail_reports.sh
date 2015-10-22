#!/bin/bash

script_dir=`dirname $0`
ft_env=${script_dir}/../etc/factools-env.sh
if [ -e $ft_env ];then
    . $ft_env
fi

mail_report=${script_dir}/../libexec/mail_report.sh
conf=$1

while read line; do
    # only consider non empty lines that aren't comments
    if [ -n "$line" ] && ! echo "$line" | grep -q '^#'; then
        $mail_report $line
    fi
done < $conf

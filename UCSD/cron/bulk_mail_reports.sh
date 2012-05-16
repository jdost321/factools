#!/bin/bash

mail_report=../libexec/mail_report.sh
conf=$1

while read line; do
    # only consider non empty lines that aren't comments
    if [ -n "$line" ] && ! echo "$line" | grep -q '^#'; then
        $mail_report $line
    fi
done < $conf

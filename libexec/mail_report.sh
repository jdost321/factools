#!/bin/bash

# Fail if reply-to is not set
if [ -z "$GLIDEIN_MAIL_REPLY_TO" ]; then
    exit 1
fi

if [ -n "$GLIDEIN_FACTORY_NAME" ];then
    factory_name="$GLIDEIN_FACTORY_NAME "
fi

# check if rpm install
if [ -e /usr/bin/analyze_entries ];then
  tools_path=/usr/bin
else
  tools_path="${GLIDEIN_SRC_DIR}/factory/tools"
  src_flag="--source $GLIDEIN_MON_URL"
fi

date=$(eval date +%m-%d-%Y)

mode=$1
shift
target=$1
shift
interval=$1
shift
emails=$1
shift

#echo $emails

case "$mode" in
    ae)
        script=analyze_entries
        if [ "$target" = factory ]; then
            out1=$(${tools_path}/${script} $src_flag -x $interval -s waste  -l wst,25 --nb)
            if [ $? -ne 0 ]; then
              echo "failed to generate factory ae sec 1"
              exit 1
            fi
            out2=$(${tools_path}/${script} $src_flag -x $interval -s waste -m)
            if [ $? -ne 0 ]; then
              echo "failed to generate factory ae sec 2"
              exit 1
            fi
            out3=$(${tools_path}/${script} $src_flag -x $interval -s waste)
            if [ $? -ne 0 ]; then
              echo "failed to generate factory ae sec 3"
              exit 1
            fi
            out=$(echo -e "${out1}\n${out2}\n${out3}")
        else
            out=$(${tools_path}/${script} $src_flag -x $interval -s waste -f $target)
            if [ $? -ne 0 ]; then
              echo "failed to generate $target ae"
              exit 1
            fi
        fi
    ;;
    aq)
        script=analyze_queues
        if [ "$target" = factory ]; then
            out1=$(${tools_path}/${script} $src_flag -x $interval -s rundiff -z -m)
            if [ $? -ne 0 ]; then
              echo "failed to generate factory aq sec 1"
              exit 1
            fi
            out2=$(${tools_path}/${script} $src_flag -x $interval -s rundiff -z)
            if [ $? -ne 0 ]; then
              echo "failed to generate factory aq sec 2"
              exit 1
            fi
            out=$(echo -e "${out1}\n${out2}")
        else
            out=$(${tools_path}/${script} $src_flag -x $interval -s rundiff -f $target -z)
            if [ $? -ne 0 ]; then
              echo "failed to generate $target aq"
              exit 1
            fi
        fi
    ;;
    aqw)
        script=analyze_queues
        out1=$(${tools_path}/${script} $src_flag -x $interval -s wait -z -m)
        if [ $? -ne 0 ]; then
          echo "failed to generate aqw sec 1"
          exit 1
        fi
        out2=$(${tools_path}/${script} $src_flag -x $interval -s wait -z)
        if [ $? -ne 0 ]; then
          echo "failed to generate aqw sec 2"
          exit 1
        fi
        out=$(echo -e "${out1}\n${out2}")
    ;;
    aqr)
        script=analyze_queues
        out1=$(${tools_path}/${script} $src_flag -x $interval -s %rundiff -z -m)
        if [ $? -ne 0 ]; then
          echo "failed to generate aqr sec 1"
          exit 1
        fi
        out1=$(${tools_path}/${script} $src_flag -x $interval -s %rundiff -z)
        if [ $? -ne 0 ]; then
          echo "failed to generate aqr sec 2"
          exit 1
        fi
        out=$(echo -e "${out1}\n${out2}")
    ;;
    af)
        script=analyze_frontends
        out=$(${tools_path}/${script} $src_flag -x $interval -s unmatched -f $target -z)
        if [ $? -ne 0 ]; then
          echo "failed to generate $target af"
          exit 1
        fi
    ;;
esac

# hack to get more specific subjects for aq reports
if [ "$mode" = "aqw" ];then
    script="Idle Wait"
elif [ "$mode" = "aqr" ];then
    script="Rundiff"
fi

if [ "$interval" = 2 ]; then
    subject="${factory_name}Factory ${script} short term report for last ${interval}h on ${date}"
else
    subject="${factory_name}Factory ${script} report for last ${interval}h on ${date}"
fi

/usr/sbin/sendmail -oi -t <<EOF
To: ${emails}
Reply-to: ${GLIDEIN_MAIL_REPLY_TO}
Subject: ${subject}
Content-Type: text/html; charset=us-ascii
Content-Transfer-Encoding: 7bit
MIME-Version: 1.0

<pre>
$out
</pre>

EOF


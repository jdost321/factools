#!/bin/bash

script_dir=`dirname $0`
ft_env=${script_dir}/../../etc/factools-env.sh
if [ -e $ft_env ];then
    . $ft_env
fi

scale=${1:-2.0}

${script_dir}/../bin/find_stale_glideins -k -f $scale

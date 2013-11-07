#!/bin/bash

source ~/.bash_profile
scale=${1:-2.0}

script_dir=`dirname $0`
${script_dir}/../bin/find_stale_glideins -k -f $scale

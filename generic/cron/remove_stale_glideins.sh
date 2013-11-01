#!/bin/bash

source ~/.bash_profile

script_dir=`dirname $0`
${script_dir}/../bin/find_stale_glideins -k

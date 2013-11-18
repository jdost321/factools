#! /bin/bash

source ~/.bash_profile

script_dir=$( cd $(dirname $0)/../bin; pwd -P )

date
echo "Running from ${script_dir}"
${script_dir}/entry_downtimes --rss 


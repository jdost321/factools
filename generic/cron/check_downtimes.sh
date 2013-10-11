#! /bin/bash

source ~/.bash_profile

script_dir=`dirname $0`
tool="${script_dir}/../bin/is_entry_in_downtime"

$tool all 


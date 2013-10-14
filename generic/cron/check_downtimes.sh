#! /bin/bash

source ~/.bash_profile

script_dir=$( cd $(dirname $0); pwd -P )
#tool="${script_dir}/../bin/is_entry_in_downtime"
tool="${script_dir}/../bin/new_entries_in_downtime"

#$tool all 
#$tool --send
$tool 


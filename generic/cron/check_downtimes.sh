#! /bin/bash

source ~/.bash_profile

script_dir=$(dirname $0)
#tool="${script_dir}/../bin/is_entry_in_downtime"
tool="${script_dir}/../bin/new_entries_in_downtime"

#$tool all 
$tool --send


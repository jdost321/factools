#! /bin/bash

source ~/.bash_profile

script_dir=$( cd $(dirname $0); pwd -P )
tool="${script_dir}/../bin/entry_downtimes"

date
$tool --updates --send all 


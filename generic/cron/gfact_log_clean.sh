#!/bin/bash

age=$1 # how many days to keep logs
src_root=$2
src_client_log_dir="${src_root}/clientlogs"
src_log_dir="${src_root}/glideinlogs"

/usr/sbin/tmpwatch -d -m $((age * 24)) $src_client_log_dir $src_log_dir

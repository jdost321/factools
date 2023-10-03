#!/bin/bash

age=$1 # how many days to keep logs
src_client_log_dir=/var/log/gwms-factory/client
src_log_dir=/var/log/gwms-factory/server
stage_dir=/var/lib/gwms-factory/web-area/stage

/usr/sbin/tmpwatch -d -m $((age * 24)) $src_client_log_dir $src_log_dir $stage_dir

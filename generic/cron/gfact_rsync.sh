#!/bin/bash

src_root=$1
dest_root=$2

src_client_log_dir="${src_root}/clientlogs"
src_log_dir="${src_root}/glideinlogs"
dest_client_log_dir="${dest_root}/clientlogs"
dest_log_dir="${dest_root}/glideinlogs"

rsync -a ${src_client_log_dir}/ $dest_client_log_dir
rsync -a --exclude '*.cifpk' --exclude '*.ftstpk' ${src_log_dir}/ $dest_log_dir

#!/bin/bash

backup_root=/backup
glidein_name="Production_v4_3"
base_client_log_dir="/var/gfactory/clientlogs"
base_log_dir="/var/gfactory/glideinlogs"
dest_client_log_dir="${backup_root}/clientlogs"
dest_log_dir="${backup_root}/glideinlogs"
opts='-a --stats'

echo "Backing up $glidein_name..."
# backup job logs
echo "Backing up job logs from $base_client_log_dir to $dest_client_log_dir..."
pushd $base_client_log_dir > /dev/null
find ./user_*/glidein_${glidein_name}/entry_* -mmin +360 -name 'job.*' > ${backup_root}/.file_list.tmp
popd > /dev/null
rsync $opts --files-from=${backup_root}/.file_list.tmp $base_client_log_dir $dest_client_log_dir

# backup condor logs
echo "Backing up condor logs from $base_client_log_dir to $dest_client_log_dir..."
pushd $base_client_log_dir > /dev/null
find ./user_*/glidein_${glidein_name}/entry_* -mmin +360 -name 'condor_activity*' > ${backup_root}/.file_list.tmp
find ./user_*/glidein_${glidein_name}/entry_* -mmin +360 -name 'submit*' >> ${backup_root}/.file_list.tmp
popd > /dev/null
rsync $opts --files-from=${backup_root}/.file_list.tmp $base_client_log_dir $dest_client_log_dir

# backup factory logs
echo "Backing up factory logs from $base_log_dir to $dest_log_dir..."
pushd $base_log_dir > /dev/null
find  ./glidein_${glidein_name}/* -mmin +360 -name 'factory.*' > ${backup_root}/.file_list.tmp
popd > /dev/null
rsync $opts --files-from=${backup_root}/.file_list.tmp $base_log_dir $dest_log_dir

# backup summary logs
echo "Backing up summary logs from $base_log_dir to $dest_log_dir..."
pushd $base_log_dir > /dev/null
find  ./glidein_${glidein_name}/* -mmin +360 -name 'completed*' > ${backup_root}/.file_list.tmp
popd > /dev/null
rsync $opts --files-from=${backup_root}/.file_list.tmp $base_log_dir $dest_log_dir

rm -f ${backup_root}/.file_list.tmp
echo "Backups complete."

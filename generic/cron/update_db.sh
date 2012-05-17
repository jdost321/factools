#!/bin/bash

script_dir=`dirname $0`
conf=${script_dir}/../etc/cms_sitedb.conf
source $conf
log_file=${log_dir}/update.log

log () {
    echo "`date +'%F %T'` ${1}" >> $log_file
}

log "Update started..."
$sdata_dir/build_xml.py > $data_dir/sitedb.xml.tmp 2>> $log_file
if [ $? -ne 0 ]; then
    log "Update failed."
    rm $data_dir/sitedb.xml.tmp
    exit 1
fi

mv $data_dir/sitedb.xml $data_dir/sitedb.old.xml
mv -f $data_dir/sitedb.xml.tmp $data_dir/sitedb.xml
log "Update finished."
log "Comparing with previous update..."
$data_dir/diff_db.py $data_dir/sitedb.old.xml $data_dir/sitedb.xml >> $log_file
log "Comparison complete."

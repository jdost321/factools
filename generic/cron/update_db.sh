#!/bin/bash

script_dir=/home/gfactory/Scripts/cms_sitedb
log_file=${script_dir}/update.log

log () {
    echo "`date +'%F %T'` ${1}" >> $log_file
}

log "Update started..."
$script_dir/build_xml.py > $script_dir/sitedb.xml.tmp 2>> $script_dir/update.log
if [ $? -ne 0 ]; then
    log "Update failed."
    rm $script_dir/sitedb.xml.tmp
    exit 1
fi

mv $script_dir/sitedb.xml $script_dir/sitedb.old.xml
mv -f $script_dir/sitedb.xml.tmp $script_dir/sitedb.xml
log "Update finished."
log "Comparing with previous update..."
$script_dir/diff_db.py $script_dir/sitedb.old.xml $script_dir/sitedb.xml >> $script_dir/update.log
log "Comparison complete."

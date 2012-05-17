#!/bin/bash

script_dir=`dirname $0`

# if any var is passed assume debug mode
if [ -n "$1" ];then
    debug=true
else
    debug=false
fi

conf=${script_dir}/../etc/cms_sitedb.conf
source $conf
log_file=${log_dir}/update.log
mkdir -p $data_dir
mkdir -p $log_dir

log () {
    echo "`date +'%F %T'` ${1}" >> $log_file
}

if $debug; then
    log "Update started..."
fi

${script_dir}/../libexec/cms_sitedb/build_xml.py > $data_dir/sitedb.xml.tmp 2>> $log_file
if [ $? -ne 0 ]; then
    log "Update failed."
    rm $data_dir/sitedb.xml.tmp
    exit 1
fi

# only do this if not first time
if [ -e $data_dir/sitedb.xml ]; then
    mv $data_dir/sitedb.xml $data_dir/sitedb.old.xml
fi

mv -f $data_dir/sitedb.xml.tmp $data_dir/sitedb.xml

if $debug; then
    log "Update finished."
fi

# only do this if not first time
if [ -e $data_dir/sitedb.old.xml ]; then
    if $debug; then
        log "Comparing with previous update..."
    fi
    out=`${script_dir}/../libexec/cms_sitedb/diff_db.py $data_dir/sitedb.old.xml $data_dir/sitedb.xml`

    if [ -n "$out" ];then
        # if not debug and have new output print date
        if ! $debug; then
            log
        fi
        echo "$out" >> $log_file
    fi

    if $debug; then
        log "Comparison complete."
    fi
fi

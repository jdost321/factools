#!/bin/bash

# this script keeps k8s factory configs up to date and is intented to run as a cron job

log() {
  echo "$(date +'%F %T') $1"
}

RUNUSER=/usr/sbin/runuser

test_repo_changed() {
  user=$1
  shift
  repo=$1
  pushd $repo
  local_hash=$($RUNUSER -u $user -- git rev-parse HEAD)
  args=$($RUNUSER -u $user -- git rev-parse --abbrev-ref @{u} | sed 's/\// /g')
  remote_hash=$($RUNUSER -u $user -- git ls-remote $args | cut -f1)
  popd
  [ $local_hash != $remote_hash ]
}

GFACTORY_REPO=/etc/osg-gfactory
AUTOCONF_DIR=/var/lib/gwms-factory/OSG_autoconf

log "Update script started; checking if factory is running..."

use_supervisor=1

supervisorctl status factory
res=$?

if [ $res -ne 0 -a $res -ne 3 ];then
  systemctl status gwms-factory
  res=$?
  use_supervisor=0
fi

if [ $res -ne 0 ];then
  log "Factory does not appear running; exiting in case someone is making changes"
  exit 0
fi

log "Checking $GFACTORY_REPO for updates..."
cd $GFACTORY_REPO

updates=0

#first check if repo has updates
# taken from https://github.com/opensciencegrid/tiger-osg-config/blob/master/manifests/base/vo-frontend-ospool/ospool-frontend-setup.sh
if test_repo_changed gfactory $GFACTORY_REPO; then
  $RUNUSER -u gfactory -- git pull || exit 1
  updates=1
  log "Updates detected and pulled; checking osg ce collector..."
else
  log "No updates in $GFACTORY_REPO detected; checking osg ce collector..."
fi

# next check if osg ce collector changes trigger updates
if [ $updates -eq 0 ];then
  rm -f /tmp/missing.yml
  rm -f /tmp/OSG.yml
  [ -e ${AUTOCONF_DIR}/missing.yml ] && cp ${AUTOCONF_DIR}/missing.yml /tmp/missing.yml
  [ -e ${AUTOCONF_DIR}/OSG.yml ] && cp ${AUTOCONF_DIR}/OSG.yml /tmp/OSG.yml

  cat > /tmp/autoconf_tmp.yaml <<EOF
MISSING_YAML: "/tmp/missing.yml" # File used to put CEs that are in the whitelist, but disappear from the OSG collector
OSG_COLLECTOR: "collector.opensciencegrid.org:9619"
OSG_YAML: "/tmp/OSG.yml" # Automatically generated from the OSG collector
OSG_DEFAULT: "${GFACTORY_REPO}/OSG_autoconf/etc/default.yml" # Default file
XML_OUTDIR: "/tmp" # Where all the output xml files will be placed
OSG_WHITELISTS: # Operator's whitelist/override files
  - "${GFACTORY_REPO}/OSG_autoconf/10-hosted-ces.auto.yml"
EOF

  OSG_autoconf /tmp/autoconf_tmp.yaml --skip-broken > /dev/null

  diff $GFACTORY_REPO/10-hosted-ces.auto.xml /tmp/10-hosted-ces.auto.xml > /dev/null
  if [ $? -ne 0 ];then
    updates=1
  fi
fi

if [ $updates -eq 0 ];then
  log "No updates found; exiting"
  exit 0
fi

log "Updates found; stopping and reconfiguring factory"

if [ $use_supervisor -eq 1 ];then
  supervisorctl stop factory
else
  systemctl stop gwms-factory
fi

/usr/sbin/gwms-factory reconfig

if [ $use_supervisor -eq 1 ];then
  supervisorctl start factory
else
  systemctl start gwms-factory
fi

log "Update completed; exiting"

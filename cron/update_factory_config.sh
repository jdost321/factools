#!/bin/bash

# this script keeps k8s factory configs up to date and is intented to run as a cron job

GFACTORY_REPO=/etc/osg-gfactory
AUTOCONF_DIR=/var/lib/gwms-factory/OSG_autoconf

cd $GFACTORY_REPO

updates=0

#first check if repo has updates
# taken from https://github.com/opensciencegrid/tiger-osg-config/blob/master/manifests/base/vo-frontend-ospool/ospool-frontend-setup.sh
if [ $(git rev-parse HEAD) != $(git ls-remote $(git rev-parse --abbrev-ref @{u} | sed 's/\// /g') | cut -f1) ]; then
  git pull || exit 1
  updates=1
else
  echo "no updates in $GFACTORY_REPO detected; checking osg ce collector..."
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

  OSG_autoconf /tmp/autoconf_tmp.yaml --skip-broken

  diff $GFACTORY_REPO/10-hosted-ces.auto.xml /tmp/10-hosted-ces.auto.xml
  if [ $? -ne 0 ];then
    updates=1
  fi
fi

if [ $updates -eq 0 ];then
  echo "no updates found; exiting"
  exit 0
fi

supervisorctl stop factory
/usr/sbin/gwms-factory reconfig
supervisorctl start factory

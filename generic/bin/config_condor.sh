#!/bin/bash

#
# Tool:
#  config_condor.sh
# 
# Arguments:
#   config_condor.sh <gwms dir> [<factools dir>]
#
# Description:
#   This script configures a Condor for a OSG factory
#
# License:
#   MIT
#   Copyright (c) 2013 Igor Sfiligoi <isfiligoi@ucsd.edu>
#


function usage {
  echo "Usage:" 1>&2
  echo " $0 <gwms dir> [<factools dir>]" 1>&2
  echo  1>&2
}

if [ $# -lt 1 ]; then
  usage
  echo "Only $# argument(s) provided" 1>&2
  exit 1
fi

GWMS=$1

if [ $# -ge 2 ]; then
   FTOOLS=$2
else
   FTOOLS=`dirname $0`/../..
fi


if [ -e "$GWMS/install/templates/00_gwms_general.config" ]; then
  true
else
  echo "Not a glideinWMS directory: $GWMS"  1>&2
  echo "File not found: $GWMS/install/templates/00_gwms_general.config" 1>&2
  exit 1
fi

#
# Do some additional basic sanity checks
#
echo 'import M2Crypto' |python
rc=$?
if [ $rc -ne 0 ]; then
  echo "Missing needed python libraries, aborting" 1>&2
  exit 1
fi

STARTDIR=$PWD

################################################
cdir=`condor_config_val LOCAL_CONFIG_DIR`
if [ $? -ne 0 ]; then
  echo "Could not find config dir" 1>&2
  exit 1
fi

# gwms templates will undefine a few attributes too many
# put local config after them
lclink="$cdir/09_condor_local.config"
lcfile=`condor_config_val LOCAL_CONFIG_FILE`
if [ $? -ne 0 ]; then
  if [ -e "$lclink" ]; then
   rm -f "$lclink"
  fi
else
  if  [ -e "$lclink" ]; then
   true
  else
   ln -s "$lcfile" "$lclink"
  fi
fi

twfile="$cdir/99_local_tweaks.config"
if [ -e "$twfile" ]; then
  true
else
  # Create an empty "tweak file", if there is none yet
  touch $cdir/99_local_tweaks.config
fi


echo "Copying the glideinWMS template config files"
echo

# now copy the base gwms templates in the config file
gtfiles="00_gwms_general.config 01_gwms_factory_collectors.config 03_gwms_local.config"

for f in $gtfiles; do
  cp $GWMS/install/templates/$f $cdir/
  if [ $? -ne 0 ]; then
    echo "Failed to copy $GWMS/install/templates/$f into $cdir" 1>&2
    exit 1
  fi
done

cp $FTOOLS/etc/condor_config/generic/02_gwms_osg_gfactory_schedd.config $cdir/
if [ $? -ne 0 ]; then
  echo "Failed to copy $FTOOLS/etc/condor_config/generic/02_gwms_osg_gfactory_schedd.config into $cdir" 1>&2
  exit 1
fi

$GWMS/install/glidecondor_createSecSched \
  schedd_glideins1,schedd_glideins2,schedd_glideins3,schedd_glideins4,schedd_glideins5,\
  schedd_glideins6,schedd_glideins7,schedd_glideins8,schedd_glideins9
rc=$?
if [ $rc -ne 0 ]; then 
    usage
    echo "Failed to setup secondary schedds" 1>&2
    exit 2
fi


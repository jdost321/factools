#!/bin/bash

#
# Tool:
#  install_condor.sh
# 
# Arguments:
#   install_condor.sh [-nolsb] <target instdir> <gwms dir> <condor tgz> [<condor user> [<factools dir>]]
#
# Description:
#   This script installs and configures a Condor for a OSG factory
#
# License:
#   MIT
#   Copyright (c) 2013 Igor Sfiligoi <isfiligoi@ucsd.edu>
#


function usage {
  echo "Usage:" 1>&2
  echo " $0 [-nolsb] <target instdir> <gwms dir> <condor tgz> [<condor user> [<factools dir>]]" 1>&2
  echo  1>&2
}

myid=`id -un`

uselsb=1
if [ "$1" == "-nolsb" ]; then
  uselsb=0
  shift
else
  if [ "$myid" != "root" ]; then
    usage
    echo "You must be root to use the lsb setup" 1>&2
    exit 1
  fi
fi

if [ $# -lt 3 ]; then
  usage
  echo "Only $# argument(s) provided" 1>&2
  exit 1
fi

INSTDIR=$1
GWMS=$2
CONDORTGZ=$3

CONDORUSER=condor
if [ $# -ge 4 ]; then
  CONDORUSER=$4
fi

if [ $# -ge 5 ]; then
   FTOOLS=$5
else
   FTOOLS=`dirname $0`/../..
fi


if [ "$myid" != "root" ]; then
  if [ "$CONDORUSER" != "$myid" ]; then
    usage
    echo "If not installing as root, must install as the condor user ($CONDORUSER!=$myid)" 1>&2
    exit 1
  fi
  OWNERSTR=""
else
  OWNERSTR="--owner=$CONDORUSER"
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

#
# Start the installation
#
if [ -d "$INSTDIR" ]; then
  e=`ls "$INSTDIR" |wc -l`
  if [ "$e" -ne "0" ]; then
    usage
    echo "Install dir exist and is not empty: $INSTDIR"
    exit 2
  fi
else
  mkdir "$INSTDIR"
  rc=$?
  if [ $rc -ne 0 ]; then 
    usage
    echo "Failed to create install dir: $INSTDIR"
    exit 2
  fi
fi

mkdir "$INSTDIR/tmp"
rc=$?
if [ $rc -ne 0 ]; then 
    usage
    echo "Failed to create tmp dir: $INSTDIR"
    exit 2
fi

STARTDIR=$PWD

tar -C "$INSTDIR/tmp" -x -z -f "$CONDORTGZ"
rc=$?
if [ $rc -ne 0 ]; then 
    usage
    echo "Failed to extract tarball: $CONDORTGZ"
    rm -fr "$INSTDIR"
    exit 2
fi

cd "$INSTDIR/tmp"
cd *
echo "In dir $PWD"
./condor_install "--prefix=$INSTDIR" "--local-dir=$INSTDIR/condor_local" --type=manager,submit $OWNERSTR
rc=$?
cd "$STARTDIR"
if [ $rc -ne 0 ]; then 
    usage
    echo "Failed to install condor"
    rm -fr "$INSTDIR"
    exit 2
fi

# we don't need the tmp dir anymore
rm -fr "$INSTDIR/tmp"

# Condor is configured to use the config dir, but does not create it
cdir=$INSTDIR/condor_local/config
mkdir $cdir
touch $cdir/90_gwms_dns.config

# We will need a dir for the mapfile
mkdir $INSTDIR/certs

cp "$GWMS/install/templates/condor_mapfile" "$INSTDIR/certs"
rc=$?
if [ $rc -ne 0 ]; then 
    echo "Failed initialize certfile"
    rm -fr "$INSTDIR"
    exit 2
fi

if [ "$uselsb" -eq 1 ]; then
  echo "procd-executable = $INSTDIR/sbin/condor_procd" > /etc/condor/privsep_config
  echo "Created basic /etc/condor/privsep_config"
  echo "You have to finish the config based on gfactory needs"
  echo 

  chmod 04755 $INSTDIR/sbin/condor_root_switchboard
  rc=$?
  if [ $rc -ne 0 ]; then 
    echo "Failed setting sticky bit to the switchboard"
    rm -fr "$INSTDIR"
    exit 2
  fi

  echo "Putting Condor in LSB locations"
  echo

  # Put everything in the standard places
  # Use the script in this repository
  "$FTOOLS/generic/bin/glidecondor_linkLSB" "$INSTDIR"
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "Failed to create LSB links" 1>&2
    echo "You may need to wipe $INSTDIR" 1>&2
    exit 1
  fi

  source /etc/profile.d/condor.sh
else
  echo "Patching configs to allow for non-LSB setup"
  echo
  cp "$FTOOLS/etc/condor_config/generic/09_gwms_local_nolsb.config" "$cdir/"
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "Failed to copy $FTOOLS/etc/condor_config/generic/09_gwms_local_nolsb.config into $cdir" 1>&2
    echo "You may need to wipe $INSTDIR" 1>&2
    exit 1
  fi

  source $INSTDIR/condor.sh
fi

"$FTOOLS/generic/bin/config_condor.sh" "$GWMS"
rc=$?
if [ $rc -ne 0 ]; then
  echo "Failed to configure condor" 1>&2
  echo "You may need to wipe $INSTDIR" 1>&2
  echo "    as well as clean the system locations" 1>&2
  exit 1
fi

if [ "$uselsb" -eq 1 ]; then
  $GWMS/install/glidecondor_addDN \
    -daemon My_hostcert_distinguished_name \
    /etc/grid-security/hostcert.pem condor
  rc=$?
  if [ $rc -ne 0 ]; then 
    echo "Failed to setup our own hostcert security"
    echo "Condor is likely misconfigured now"
    exit 2
  fi

  echo "Condor will be in the path next time you log back in"
  echo "You can control the daemons with"
  echo "  /etc/init.d/condor start|stop"
else
  $GWMS/install/glidecondor_addDN \
    -daemon My_hostcert_distinguished_name \
    ~/.globus/hostcert.pem condor
  rc=$?
  if [ $rc -ne 0 ]; then 
    echo "Failed to setup our own hostcert security"
    echo "Condor is likely misconfigured now"
    exit 2
  fi

  echo "Note: Condor not in the path"
  echo "      You may need to source $INSTDIR/condor.sh"
fi

exit 0

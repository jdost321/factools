#!/bin/bash

#
# Input: GLIDEIN_REQUIRED_OS
#
# Acceptable values:
#   rhel4 - RedHat EL4 compatible OS
#   rhel5 - RedHat EL5 compatible OS
#   rhel6 - RedHat EL6 compatible OS
#   rhel7 - RedHat EL7 compatible OS
#   any   - do not test
# 


##################
# Standard glidein scrip stuff
##################

glidein_config="$1"
add_config_line_source=`awk '/^ADD_CONFIG_LINE_SOURCE /{print $2}' $glidein_config`
source $add_config_line_source

condor_vars_file=`grep -i "^CONDOR_VARS_FILE " $glidein_config | awk '{print $2}'`


#################
# Functions
#################

function check_rhel {
  req_os=$1
  
  echo "Requesting RHEL variant '$req_os'"

  if [ -f /etc/redhat-release ]; then
    echo "RHEL Linux flavor found"
    cat /etc/redhat-release

    case "$req_os" in
      rhel4 ) v=4 ;;
      rhel5 ) v=5 ;;
      rhel6 ) v=6 ;;
      rhel7 ) v=7 ;;
      * ) echo "Unsupported GLIDEIN_REQUIRED_OS RHEL variant '$req_os'"; exit 1;;
    esac

    grep -qi " release $v" /etc/redhat-release
    res=$?

    if [ "$res" -eq 0 ]; then
      echo "Passing test for $req_os"
      return 0
    else
      echo "Failed OS test for $req_os"
      exit 1
    fi

  else
    echo "Requested RHEL but /etc/redhat-release not found"
    exit 1
  fi

  # just as a fail safe protection
  exit 1
} 

#################
# Meat
#################

req_os=`grep -i "^GLIDEIN_REQUIRED_OS " $glidein_config | awk '{print $2}'`

if [ -z "$req_os" ]; then
  echo "No OS requirements found, passing by default"
  exit 0
fi

case "$req_os" in
    rhel* ) check_rhel "$req_os";;
    any ) echo "Any OS OK, passing by default";;
    * ) echo "Unsupported GLIDEIN_REQUIRED_OS '$req_os'";exit 1;;
esac

echo "OS test passed"
exit 0

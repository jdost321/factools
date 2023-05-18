#!/bin/bash

##################
# Standard glidein script stuff
##################

glidein_config="$1"
add_config_line_source=`awk '/^ADD_CONFIG_LINE_SOURCE /{print $2}' $glidein_config`
source $add_config_line_source

condor_vars_file=`grep -i "^CONDOR_VARS_FILE " $glidein_config | awk '{print $2}'`

echo "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
cat $glidein_config
echo "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"


#######
# Get VO name
#######
vo_name=`awk '/^GLIDECLIENT_OSG_VO /{print $2}' $glidein_config`
if [ -z "${vo_name}" ]; then
  # VO did not identify itself, nothing to do
  echo "define_OSG_SE: VO did not identify itself.. nothing to do"
  exit 0
fi
echo "define_OSG_SE: VO name is ${vo_name}"

search_expr="n=split(\$2,a,\",\"); found=\"\"; for (i=1;i<=n;i++) {if (a[i]==\"${vo_name}\") {found=\"${vo_name}\"; break;}} print found"
bpvo=`awk "/^VOS_USING_SE_BASEPATH /{${search_expr}}" $glidein_config`
if [ -n "$bpvo" ]; then
 sepath=`awk '/^GLIDEIN_SE_BASEPATH /{print $2}' $glidein_config`
 echo "define_OSG_SE/BASEPATH: $sepath"
else
 lcvo=`awk "/^VOS_USING_SE_VONAME_LOWERCASE /{${search_expr}}" $glidein_config`
 if [ -n "$lcvo" ]; then
   awk_expr="print \$2 \"/\" tolower(\"${vo_name}\")"
   sepath=`awk "/^GLIDEIN_SE_VONAME_LOWERCASE /{${awk_expr}}" $glidein_config`
   echo "define_OSG_SE/LOWERCASE: $sepath"
 else
  osvo=`awk "/^VOS_USING_SE_OTHER_SUBDIR /{${search_expr}}" $glidein_config`
  if [ -n "$osvo" ]; then 
    sepath=`awk "/^GLIDEIN_SE_PATH_${vo_name} /{print \\$2}" $glidein_config`
    echo "define_OSG_SE/OTHER: $sepath"
  else
   # not listed in any rule, nothing to do
   # may want to change this in the future
   echo "define_OSG_SE: no rule found.. nothing to do"
   exit 0
  fi
 fi
fi

if [ -z "$sepath" ]; then
  # rule expected, but then not found
  echo "define_OSG_SE: rule not found!" 1>&2
  exit 1
fi


add_config_line "GLIDEIN_LOCAL_SITE_SE" "$sepath"
add_condor_vars_line "GLIDEIN_LOCAL_SITE_SE" "S" "-" "+" "Y" "Y" "+"

exit 0

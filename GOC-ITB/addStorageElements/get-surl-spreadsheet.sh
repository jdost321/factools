#!/bin/sh

while read line
do

if [ `echo $line | egrep "^VO="`  ]; then
  vo=`echo $line | sed -e 's/VO=//g'`
  continue
fi
site=`echo $line | sed -e 's?srm://??g' -e 's?:.*??g'`
echo -e "$site\t$vo\t$line"

done < "all-surl.dat"


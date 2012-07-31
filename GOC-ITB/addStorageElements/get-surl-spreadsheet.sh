#!/bin/sh

#vos='Accelerator ALICE Argoneut ATLAS belle CDF Cdms CIGI CMS CompBioGrid CSIU DayaBay DES DOSAR DREAM DZero Engage enmr.eu FermiGrid Fermilab FermilabLbne FermiTest GCEDU GCVO geant4 GLOW Gluex gm2 GPN GridUNESP GROW HCC i2u2 IceCube ILC LBNE LIGO MAP mars MicroBooNE Minerva Miniboone Minos Mipp MIS Mu2e nanoHUB NEBioGrid NEES NERSC Nova Numi NWICG NYSGRID Ops OSG OSGEDU Patriot SBGrid STAR superbvo.org SURAGrid Theory'

vos="ATLAS CDF CMS Engage GLOW Gluex HCC nanoHUB NEBioGrid NEES NWICG OSG"

#if [ -z "$VDT_LOCATION" ]; then
#  echo "ERROR: setup up VDT" 1>&2
#  exit 1
#fi

for vo in $vos
do
#  echo "VO=$vo"
  for surl in `get_surl --vo $vo`
  do
    if [ `echo $surl | egrep "^VO="` ]; then
      vo=`echo $surl | sed -e 's/VO=//g'`
#      continue
    fi
  site=`echo $surl | sed -e 's?srm://??g' -e 's?:.*??g'`
  output+="$site"$'\t'"$vo"$'\t'"$surl"$'\n'
  done
done

#echo "$output" | sort
echo "$output" | sort

exit

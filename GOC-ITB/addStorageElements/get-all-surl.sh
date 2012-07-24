#!/bin/sh
vos='Accelerator ALICE Argoneut ATLAS belle CDF Cdms CIGI CMS CompBioGrid CSIU DayaBay DES DOSAR DREAM DZero Engage enmr.eu FermiGrid Fermilab FermilabLbne FermiTest GCEDU GCVO geant4 GLOW Gluex gm2 GPN GridUNESP GROW HCC i2u2 IceCube ILC LBNE LIGO MAP mars MicroBooNE Minerva Miniboone Minos Mipp MIS Mu2e nanoHUB NEBioGrid NEES NERSC Nova Numi NWICG NYSGRID Ops OSG OSGEDU Patriot SBGrid STAR superbvo.org SURAGrid Theory'

if [ -z "$VDT_LOCATION" ]; then
  echo "ERROR: setup up VDT" 1>&2
  exit 1
fi

for vo in $vos
do
 echo "VO=$vo"
 get_surl --vo $vo
done


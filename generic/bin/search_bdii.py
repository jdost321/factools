#!/usr/bin/python

import os, sys, getopt

#sys.path.append(os.path.join(STARTUP_DIR,"../../../"))

# get source dir from env var until we push upstream to glideinWMS
if 'GLIDEIN_SRC_DIR' in os.environ:
    sys.path.append(os.path.join(os.environ['GLIDEIN_SRC_DIR'],"../"))
else:
    print '"GLIDEIN_SRC_DIR" not defined. exiting.'
    sys.exit(1)

from glideinwms.lib import ldapMonitor

def search(bdii_url, bdii_port=None, infosysref=None, vo=None, ce=None, ldap_search=None, search_string=None):
    SearchBDII=ldapMonitor.SearchBDII(bdii_url, bdii_port, vo, ce, infosysref, ldap_search, search_string)
    SearchBDII.query_bdii()
    SearchBDII.search_bdii_data()
    SearchBDII.display_bdii_data()


def usage(exit='y'):
    print "Usage: search_bdii_v0.py [options] [args]"
    print "-b   (bdii url)"
    print "   possible options are exp-bdii.cern.ch"
    print "                        is.grid.iu.edu"
    print "-s   (search string)"
    print "-l   (ldap search string)"
    print "-v   (vo)"
    print "-p   (port number) defaults 2170"    
    print "-i   (infosysref)  usually starts \"GlueUniqueID\""
    print "-c   (ce)  usually don't include ce's port number"
    print "use -h or --help"
    print "TO BE ADDED"
    print "More efficient search"
    print "Change search port"
    print "Other ldap search options"
    if exit=='y':
        sys.exit(0)

if __name__=="__main__":
    
    opts,args=getopt.getopt(sys.argv[1:],'hs:b:p:v:l:i:c:', ['help'])
    search_string=None
    ce=None
    vo=None
    ldap_search=None
    infosysref=None
    
    bdii_url=None
    bdii_port=None #this variable doesn't do anything yet
    for opt in opts:
        if opt[0]=='-h' or opt[0]=='--help':
            usage()
        if opt[0]=='-s':
            search_string=opt[1]
        if opt[0]=='-b':
            bdii_url=opt[1]
        if opt[0]=='-p':
            bdii_port=opt[1]
        if opt[0]=='-c':
            ce=opt[1]
        if opt[0]=='-l':
            ldap_search=opt[1]
        if opt[0]=='-v':
            vo=opt[1]
        if opt[0]=='-i':
            infosysref=opt[1]


    search(bdii_url, bdii_port, infosysref, vo, ce, ldap_search, search_string)
    if not bdii_url:
        usage()
    
    

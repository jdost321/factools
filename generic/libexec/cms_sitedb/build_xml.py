#!/usr/bin/python

import sys
import urllib2

db_url="https://cmsweb.cern.ch/sitedb/json/index"

# may raise urllib2.URLError
def print_ces(site_name):
    fin = urllib2.urlopen("%s/CMSNametoCE?name=%s" % (db_url,site_name))
    name2ce_json =  eval(fin.read())
    fin.close()
    ce_list = []
    for i in name2ce_json:
        # ce might be a comma separated list
        ces = name2ce_json[i]['name'].split(',')
        for ce in ces:
            # i've seen duplicates in sitedb
            if not ce in ce_list:
                ce_list.append(ce.strip())
    ce_list.sort()
    for ce in ce_list:
        print "      <CE>%s</CE>" % ce

# may raise urllib2.URLError
def print_ses(site_name):
    fin = urllib2.urlopen("%s/CMSNametoSE?name=%s" % (db_url,site_name))
    name2se_json =  eval(fin.read())
    fin.close()
    se_list = []
    for i in name2se_json:
        # se might be a comma separated list
        ses = name2se_json[i]['name'].split(',')
        for se in ses:
            # i've seen duplicates in sitedb
            if not se in se_list:
                se_list.append(se.strip())
    se_list.sort()
    for se in se_list:
        print "      <SE>%s</SE>" % se

try:
    fin = urllib2.urlopen("%s/CEtoCMSName?name" % db_url)
except urllib2.URLError:
    sys.stderr.write("ERROR: Failed to open initial site list.\n")
    sys.exit(1)

ce2name_json = eval(fin.read())
#print ce2name_json
fin.close()

site_list = []
for i in ce2name_json:
    if ce2name_json[i]['name'] not in site_list:
        site_list.append(ce2name_json[i]['name'])
site_list.sort()
#print len(site_list)
#print site_list

print "<sites>"
for site_name in site_list:
#for i in range(3):
#    site_name = site_list[i]
    print "  <site name=\"%s\">" % site_name
    print "    <CEs>"
    try:
        print_ces(site_name)
        #raise urllib2.URLError("fake")
    except urllib2.URLError:
        sys.stderr.write("ERROR: Failed opening CE list for %s.\n" % site_name)
        sys.exit(1)
    print "    </CEs>"
    print "    <SEs>"
    try:
        print_ses(site_name)
    except urllib2.URLError:
        sys.stderr.write("ERROR: Failed opening SE list for %s.\n" % site_name)
        sys.exit(1)
    print "    </SEs>"
    print "  </site>"
print "</sites>"

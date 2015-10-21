#!/usr/bin/python

# WARNING work in progress.  have to finish modifying parse_bdii to account for entries with identical unique id's
import sys
import os
import re
import time
import calendar

if 'GLIDEIN_SRC_DIR' in os.environ:
    sys.path.append(os.path.join(os.environ['GLIDEIN_SRC_DIR'], "../"))

from glideinwms.creation.lib import cgWParams
from glideinwms.lib import ldapMonitor

def get_bad_entries(unique_ids, key, b_entry):
    bad_entries = None
    for e in unique_ids[key]['entries']:
        if unique_ids[key]['entries'][e] is None:
            if bad_entries is None:
                bad_entries = []
            bad_entries.append(e)
        else:
            ent_dn = unique_ids[key]['entries'][e][0]
            if ent_dn != b_entry:
                if bad_entries is None:
                    bad_entries = []
                bad_entries.append(e)

    return bad_entries

# bdii_data_list is a list of bdii results from different servers
def get_bad_condor_entries(unique_ids, key, bdii_data_list):
    bad_entries = None
    for e in unique_ids[key]['entries']:
        if unique_ids[key]['entries'][e] is None:
            if bad_entries is None:
                bad_entries = []
            bad_entries.append(e)
        else:
            ent_dn = unique_ids[key]['entries'][e][0]
            good = False
            
            # check if dn is a key in any bdii server
            for s in bdii_data_list:
                if ent_dn in s:
                    good = True
                    break
            if not good:
                if bad_entries is None:
                    bad_entries = []
                bad_entries.append(e)

    return bad_entries

def is_real_dn(unique_ids, key, dn):
    real = False
    for rd in unique_ids[key]['real_dn']:
        if dn == rd[0]:
            real = True
            break
    return real

# other_bdii_data - still need to check against all db's if condor..maybe it should be
# made an optional list to be more reusable later
def parse_bdii(bdii_data, other_bdii_data, server, unique_ids, bad_bdii_entries):
    errors = 0
    for b_entry in bdii_data.keys():
        # basic error handling, should be improved
        if not 'GlueCEInfoHostName' in bdii_data[b_entry]:
            continue

        host = bdii_data[b_entry]['GlueCEInfoHostName'][0]
        jm = bdii_data[b_entry]['GlueCEInfoJobManager'][0]

        if jm == 'condor':
            if host not in b_entry or jm not in b_entry:
                bad_bdii_entries[b_entry] = (host, jm)
                continue
            key = "%s,%s" % (host, jm)
        else:
            queue = bdii_data[b_entry]['GlueCEName'][0]
            if jm != 'arc' and (host not in b_entry or jm not in b_entry or queue not in b_entry):
                bad_bdii_entries[b_entry] = (host, jm, queue)
                continue
            key = "%s,%s,%s" % (host, jm, queue)

        if key in unique_ids:
            if not unique_ids[key]['found']:
                unique_ids[key]['found'] = True
                # just ignore condor we don't expect the dn to be the same
                #if jm != 'condor' and unique_ids[key]['dn'] != b_entry:
                if jm != 'condor':
                    bad_entries = get_bad_entries(unique_ids, key, b_entry)
                    if bad_entries is not None:
                        errors += len(bad_entries)
                        unique_ids[key]['real_dn'] = []
                        unique_ids[key]['real_dn'].append((b_entry,server))
                # in condor call it an error if the key isn't in bdii at all
                #elif jm == 'condor' and unique_ids[key]['dn'] not in bdii_data and unique_ids[key]['dn'] not in other_bdii_data:
                else:
                    bad_entries = get_bad_condor_entries(unique_ids, key, [bdii_data, other_bdii_data])
                    if bad_entries is not None:
                        errors += len(bad_entries)
                        unique_ids[key]['real_dn'] = []
                        unique_ids[key]['real_dn'].append((b_entry,server))
            # collect more dns if it is a match condor and already found (only if not taken already from osg)
            elif jm == 'condor' and 'real_dn' in unique_ids[key] and not b_entry in [dn for dn,server in unique_ids[key]['real_dn']]:
                unique_ids[key]['real_dn'].append((b_entry,server))

    return errors

if 'GLIDEIN_FACTORY_DIR' in os.environ:
    gfactory_dir=os.environ['GLIDEIN_FACTORY_DIR']
# try rpm location
elif os.path.isdir('/var/lib/gwms-factory/work-dir'):
    gfactory_dir='/var/lib/gwms-factory/work-dir'
else:
    gfactory_dir="."

down_file_path = os.path.join(gfactory_dir, "glideinWMS.downtimes")

try:
    down_file = open(down_file_path)
except IOError:
   sys.stderr.write('"%s" not a valid factory dir. Exiting.\n' % gfactory_dir)
   sys.exit(1)    

try:
    down_entries = set()
    for line in down_file:
        #print line
        if line.startswith("#"):
            continue
        line = line.split()
        if len(line) < 3:
            continue
        end = line[1]
        entry = line[2]
        if end == "None":
            down_entries.add(entry)
        else:
            offset = int(end[-6:].split(':')[0])
            end_seconds = calendar.timegm(time.strptime(end[:-6], "%Y-%m-%dT%X"))
            end_seconds -= offset * 3600
            if end_seconds > time.time():
                down_entries.add(entry)

finally:
    down_file.close()

conf = sys.argv[1]
cparams=cgWParams.GlideinParams("","",["",conf])
server_osg="is.grid.iu.edu"
server_cern="exp-bdii.cern.ch"
bdii_obj=ldapMonitor.BDIICEQuery(bdii_url=server_osg)
bdii_data=bdii_obj.fetch()
bdii_obj=ldapMonitor.BDIICEQuery(bdii_url=server_cern)
bdii_data2=bdii_obj.fetch()


''' browse bdii to see condor queue names
for k in bdii_data2:
    if bdii_data2[k]['GlueCEInfoJobManager'][0] == "condor":
        print k
'''

unique_ids = {}
for entry in cparams.entries.keys():
    if eval(cparams.entries[entry]['enabled']):
        # for now skip cream and nordugrid
        if cparams.entries[entry]['gridtype'] == 'cream':
            gk = cparams.entries[entry]['gatekeeper'].split()
            
            # handle new format
            if len(gk) == 1:
                host, rest = gk[0].split(':8443/cream-')
                jm, queue = rest.split('-')
            else:
                contact = gk[0]
                if 'https' in contact:
                    contact = contact[8:]
                host = contact.split(':')[0]
                jm = gk[-2]
                queue = gk[-1]
            key = "%s,%s,%s" % (host,jm,queue)
        else:
            host = cparams.entries[entry]['gatekeeper'].split(':')[0]
            if cparams.entries[entry]['gridtype'] == 'nordugrid':
                jm = "arc"
            else:
                jm = cparams.entries[entry]['gatekeeper'].split('-')[-1]
            rsl = cparams.entries[entry]['rsl']
            if jm == "condor":
                key = "%s,%s" % (host,jm)
            else:
                if rsl is not None and "queue" in rsl:
                    queue = re.search(r"queue=([^)]+)", rsl).group(1)
                # try pulling queue from infosys if there
                elif len(cparams.entries[entry]['infosys_refs']) > 0:
                    dn = cparams.entries[entry]['infosys_refs'][0]['ref']
                    queue = dn.split(',')[0].split('-')[-1]
                    #print "%s %s" % (entry, queue)
                else:
                    # finally just assume default if queue not specified
                    queue = 'default'
                key = "%s,%s,%s" % (host,jm,queue)
        if key not in unique_ids:
            unique_ids[key] = {}
            # to figure out who we visited later
            unique_ids[key]['found'] = False
            #unique_ids[key]['name'] = entry

            # list needed for multiple entries with same unique id
            unique_ids[key]['entries'] = {}

        if len(cparams.entries[entry]['infosys_refs']) > 0: 
            #unique_ids[key]['dn'] = cparams.entries[entry]['infosys_refs'][0]['ref']
            unique_ids[key]['entries'][entry] = (cparams.entries[entry]['infosys_refs'][0]['ref'],cparams.entries[entry]['infosys_refs'][0]['server'])
        else:
            unique_ids[key]['entries'][entry] = None
            

#for e in entries:
#    print "%s %s %s" % (e, entries[e]['name'], entries[e]['dn'])

bad_bdii_entries = {}
# first is.grid
errors = parse_bdii(bdii_data, bdii_data2, server_osg, unique_ids, bad_bdii_entries)
# next cern
errors = errors + parse_bdii(bdii_data2, bdii_data, server_cern, unique_ids, bad_bdii_entries)

incorrect = []
missing = []
down = []
verified = []
corrupt_bdii = []
tot_found = 0
tot_missing = 0

for key in unique_ids:
    if 'real_dn' in unique_ids[key]:
        #print '%s\n"%s"\n"%s"\n' % (entries[e]['name'], entries[e]['dn'], entries[e]['real_dn'])
        for ent in unique_ids[key]['entries']:
            if unique_ids[key]['entries'][ent] is None:
                ent_dn = None
            else:
                ent_dn = unique_ids[key]['entries'][ent][0]

            # not all entries with this key are wrong so check
            if not is_real_dn(unique_ids, key, ent_dn):
                incorrect.append((ent, ent_dn, unique_ids[key]['real_dn']))
                '''print '%s\ncurrent:\n"%s"' % (ent, ent_dn)
                print 'correct:'
                for dn in unique_ids[key]['real_dn']:
                    print '"%s" %s' % dn
                print
                '''
        
    if unique_ids[key]['found']:
        tot_found += len(unique_ids[key]['entries'])
    else:
        tot_missing += len(unique_ids[key]['entries'])
        for ent in unique_ids[key]['entries']:
            if unique_ids[key]['entries'][ent] is None:
                ent_dn = None
            else:
                ent_dn = unique_ids[key]['entries'][ent][0]
           
            # if bdii had bad info, the script was confused. just recount as found
            if ent_dn in bad_bdii_entries:
                corrupt_bdii.append((ent, ent_dn, bad_bdii_entries[ent_dn]))
                tot_found += 1
                tot_missing -= 1
            elif ent in down_entries:
                down.append((ent, ent_dn))
            elif ent_dn is not None and 'verified' in ent_dn.lower():
                verified.append((ent, ent_dn))
            else:
                missing.append((ent, ent_dn))
                #print '%s "%s"' % (ent, ent_dn)

incorrect.sort()
missing.sort()
verified.sort()
down.sort()
corrupt_bdii.sort()

print "Entries with incorrect infosys"
print "------------------------------\n"
for res in incorrect:
    print '%s\ncurrent:\n"%s"' % (res[0], res[1])
    print 'correct:'
    for dn in res[2]:
        print '"%s" %s' % dn
    print

print "Entries not found in bdii"
print "-------------------------\n"
for res in missing:
    print '%s "%s"' % (res[0], res[1])

print "\nEntries not in bdii but verified to work"
print "----------------------------------------\n"
for res in verified:
    print '%s "%s"' % (res[0], res[1])

print "\nEntries in downtime not found in bdii"
print "-------------------------------------\n"
for res in down:
    print '%s "%s"' % (res[0], res[1])

print "\nEntries with valid bdii dn but corrupt bdii info"
print "------------------------------------------------\n"
for res in corrupt_bdii:
    print '%s "%s"' % (res[0], res[1])
    print "GlueCEInfoHostName: %s" % res[2][0]
    print "GlueCEInfoJobManager: %s" % res[2][1]
    if len(res[2]) == 3:
        print "GlueCEName: %s" % res[2][2]    
    print

print "\ntotal unique: %s\nfound: %s\nmissing: %s\nincorrect: %s" % (len(unique_ids),tot_found,tot_missing,errors)

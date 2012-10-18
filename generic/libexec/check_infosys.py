#!/usr/bin/python

# WARNING work in progress.  have to finish modifying parse_bdii to account for entries with identical unique id's
import sys
import os
import re

if 'GLIDEIN_SRC_DIR' in os.environ:
    sys.path.append(os.path.join(os.environ['GLIDEIN_SRC_DIR'], "lib"))
    sys.path.append(os.path.join(os.environ['GLIDEIN_SRC_DIR'], "creation/lib"))
else:
    print '"GLIDEIN_SRC_DIR" not defined. exiting.'
    sys.exit(1)

import cgWParams
import ldapMonitor

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

def is_real_dn(unique_ids, key, dn):
    real = False
    for rd in unique_ids[key]['real_dn'][0]:
        if dn == rd:
            real = True
            break
    return real

# other_bdii_data - still need to check against all db's if condor..maybe it should be
# made an optional list to be more reusable later
def parse_bdii(bdii_data, other_bdii_data, server, unique_ids):
    errors = 0
    for b_entry in bdii_data.keys():
        host = bdii_data[b_entry]['GlueCEInfoHostName'][0]
        jm = bdii_data[b_entry]['GlueCEInfoJobManager'][0]

        if jm == 'condor':
            key = "%s,%s" % (host, jm)
        else:
            queue = bdii_data[b_entry]['GlueCEName'][0]
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

conf = sys.argv[1]
cparams=cgWParams.GlideinParams("dummy",os.path.join(os.environ['GLIDEIN_SRC_DIR'],"creation/web_base"),["dummy",conf])
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
                # this assumes there is no valid '-' in queue name
                gk = gk[0].split('-')
                host = gk[0]
                jm = gk[1]
                queue = gk[2]
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
                    queue = re.search(r"queue=(\w+)\)", rsl).group(1)
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

print "Entries with incorrect infosys"
print "------------------------------\n"
# first is.grid
errors = parse_bdii(bdii_data, bdii_data2, server_osg, unique_ids)
# next cern
errors = errors + parse_bdii(bdii_data2, bdii_data, server_cern, unique_ids)

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
                print '%s\ncurrent:\n"%s"' % (ent, ent_dn)
                print 'correct:'
                for dn in unique_ids[key]['real_dn']:
                    print '"%s" %s' % dn
                print
        
tot_found = 0
tot_missing = 0
print "Entries not found in bdii"
print "-------------------------\n"
for key in unique_ids:
    if unique_ids[key]['found']:
        tot_found += len(unique_ids[key]['entries'])
    else:
        tot_missing += len(unique_ids[key]['entries'])
        for ent in unique_ids[key]['entries']:
            if unique_ids[key]['entries'][ent] is None:
                ent_dn = None
            else:
                ent_dn = unique_ids[key]['entries'][ent][0]
            print '%s "%s"' % (ent, ent_dn)

print "\ntotal unique: %s\nfound: %s\nmissing: %s\nincorrect: %s" % (len(unique_ids),tot_found,tot_missing,errors)

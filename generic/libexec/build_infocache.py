#!/usr/bin/python

import ldap
import sys
import htcondor
import re
import pickle

VOS = ['vo:cdf','voms:/cdf','voms:/cdf/*',
           'vo:cigi',
           'vo:cms','voms:/cms','voms:/cms/*',
           'vo:fermilab',
           'vo:glow',
           'vo:gluex',
           'vo:hcc','voms:/hcc','voms:/hcc/*',
           'vo:lsst',
           'vo:nanohub',
           'vo:nees',
           'vo:osg',
           'vo:sbgrid',
           'vo:uc3']
VO_PATTERNS = ['vo:cdf$|voms:/cdf$|voms:/cdf/',
           'vo:cigi$',
           'vo:cms$|voms:/cms$|voms:/cms/',
           'vo:fermilab$',
           'vo:glow$',
           'vo:gluex$',
           'vo:hcc$|voms:/hcc$|voms:/hcc/',
           'vo:lsst$',
           'vo:nanohub$',
           'vo:nees$',
           'vo:osg$',
           'vo:sbgrid$',
           'vo:uc3$']

VO_FULL_PATTERN = '|'.join(VO_PATTERNS)
VO_REGEX = re.compile(VO_FULL_PATTERN, re.I)

# string manip to extract hostname in GLUE2
# serv_id is GLUE2ServiceID
# serv_type is GLUE2ServiceType
# currently supports cream, nordugrid, gram
def get_glue2_hostname(serv_id, serv_type):
    if serv_type == 'org.glite.ce.CREAM':
      if serv_id.endswith('_ComputingElement'):
        return serv_id[:-17]
      else:
        return serv_id
    elif serv_type == 'org.nordugrid.arex':
      return serv_id.split(':')[3]
    else:
      if serv_id.endswith('_ComputingEntity'):
        return serv_id[:-16]
      else:
        return serv_id

# return list of queue mappings of given CE dn that matches vo regex
def get_glue2_vo_mappings(ldap_obj, dn, vo_regex):
  vo_res = ldap_obj.search_s(dn, ldap.SCOPE_SUBTREE, '(objectclass=GLUE2MappingPolicy)', attrlist=['GLUE2PolicyRule'])
  mappings = []
  for vr in vo_res:
    vos = []
    for rule in vr[1]['GLUE2PolicyRule']:
      if vo_regex.match(rule):
        vos.append(rule)
    if len(vos) > 0:
      mappings.append((vr[0], vos))

  return mappings

def get_glue2_hosts(bdii_serv):
  l = ldap.open(bdii_serv, 2170)

  l.simple_bind_s('','')
  res = l.search_s('GLUE2GroupID=grid,o=glue', ldap.SCOPE_SUBTREE, '(&(objectClass=GLUE2ComputingService)(|(GLUE2ServiceType=org.glite.ce.CREAM)(GLUE2ServiceType=org.nordugrid.arex)(GLUE2ServiceType=org.globus.gram)))',attrlist=['GLUE2ServiceID','GLUE2ServiceType'])

  hosts = {}
  for r in res:
    dn = r[0]
    vo_mappings = get_glue2_vo_mappings(l, dn, VO_REGEX)
    if len(vo_mappings) == 0:
      continue

    queues = {}
    for vo_map in vo_mappings:
      dn_arr = vo_map[0].split(',')
      share_dn = ','.join(dn_arr[1:])
      q_name = l.search_s(share_dn, ldap.SCOPE_BASE, attrlist=['GLUE2ComputingShareMappingQueue'])[0][1]['GLUE2ComputingShareMappingQueue'][0]
      if q_name not in queues:
        queues[q_name] = []

      queues[q_name] += vo_map[1]
      serv_type = r[1]['GLUE2ServiceType'][0]
      if serv_type == 'org.glite.ce.CREAM':
        gt = 'cream'
      elif serv_type == 'org.nordugrid.arex':
        gt = 'nordugrid'
      else:
        gt = 'gt5'

      hosts[get_glue2_hostname(r[1]['GLUE2ServiceID'][0],r[1]['GLUE2ServiceType'][0])] = {'queues': queues, 'gridtype': gt}

  l.unbind()
  return hosts

def get_glue1_hosts(bdii_serv):
  l = ldap.open(bdii_serv, 2170)

  l.simple_bind_s('','')
  res = l.search_s('Mds-Vo-name=local,o=grid', ldap.SCOPE_SUBTREE, '(&(objectClass=gluece)(|(GlueCEImplementationName=cream)(GlueCEImplementationName=arc-ce)(GlueCEImplementationName=globus)))', attrlist=['GlueCEAccessControlBaseRule','GlueCEInfoHostName','GlueCEName','GlueCEImplementationName'])

  l.unbind()

  hosts = {}
  for r in res:
    vos = []
    for rule in r[1]['GlueCEAccessControlBaseRule']:
      if VO_REGEX.match(rule):
        vos.append(rule)
    if len(vos) == 0:
      continue

    host = r[1]['GlueCEInfoHostName'][0]
    if host not in hosts:
      ce_imp = r[1]['GlueCEImplementationName'][0]
      if ce_imp.lower() == 'cream':
        gt = 'cream'
      elif ce_imp.lower() == 'arc-ce':
        gt = 'nordugrid'
      else:
        gt = 'gt5'

      hosts[host] = {'queues':{},'gridtype': gt}

    hosts[host]['queues'][r[1]['GlueCEName'][0]] = vos

  return hosts

def get_osg_hosts(coll_serv):
  col = htcondor.Collector("%s:9619" % coll_serv)
  res = col.query(htcondor.AdTypes.Schedd, "true", ['Name'])
  hosts = set()
  hosts = {}
  for r in res:
    hosts[r['Name']] = {'queues':{}, 'gridtype':'condor'}

  return hosts
  
# order matters. last queries overwrite previous ce info
# so save most relevant calls for last
hosts = get_glue1_hosts('exp-bdii.cern.ch')
hosts.update(get_glue1_hosts('is.grid.iu.edu'))
hosts.update(get_glue2_hosts('exp-bdii.cern.ch'))
hosts.update(get_osg_hosts('collector.opensciencegrid.org'))

'''for h in hosts:
  print h
  print hosts[h]['gridtype']
  for q in hosts[h]['queues']:
    print "%s: %s" % (q,hosts[h]['queues'][q])
  print
'''
  
fout = open('infocache.pkl','w')
pickle.dump(hosts, fout)
fout.close()


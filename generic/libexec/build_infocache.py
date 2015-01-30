#!/usr/bin/python

import ldap
import sys
import htcondor
import re
import pickle

VO_REGEXES = {'cdf': re.compile('vo:cdf$|voms:/cdf$|voms:/cdf/', re.I),
           'cigi': re.compile('vo:cigi$', re.I),
           'cms': re.compile('vo:cms$|voms:/cms$|voms:/cms/', re.I),
           'fermilab': re.compile('vo:fermilab$', re.I),
           'glow': re.compile('vo:glow$', re.I),
           'gluex': re.compile('vo:gluex$', re.I),
           'hcc': re.compile('vo:hcc$|voms:/hcc$|voms:/hcc/', re.I),
           'lsst': re.compile('vo:lsst$', re.I),
           'nanohub': re.compile('vo:nanohub$', re.I),
           'nees': re.compile('vo:nees$', re.I),
           'osg': re.compile('vo:osg$', re.I),
           'sbgrid': re.compile('vo:sbgrid$', re.I),
           'uc3': re.compile('vo:uc3$', re.I)}

JM_REGEXES = {'pbs': re.compile('pbs$|torque$', re.I),
            'condor': re.compile('condor$', re.I),
            'slurm': re.compile('slurm$', re.I),
            'sge': re.compile('sge$|sungridengine$', re.I)}

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
def get_glue2_vo_mappings(ldap_obj, dn):
  vo_res = ldap_obj.search_s(dn, ldap.SCOPE_SUBTREE, '(objectclass=GLUE2MappingPolicy)', attrlist=['GLUE2PolicyRule'])
  mappings = []
  for vr in vo_res:
    vos = set()
    for rule in vr[1]['GLUE2PolicyRule']:
      for vo in VO_REGEXES:
        if VO_REGEXES[vo].match(rule):
          vos.add(vo)
          break
    if len(vos) > 0:
      mappings.append((vr[0], vos))

  return mappings

def get_glue2_q_attrs(ldap_obj, dn, gridtype):
  contact_str = None

  if gridtype == 'cream':
    res = ldap_obj.search_s(dn, ldap.SCOPE_BASE, attrlist=['GLUE2ComputingShareMappingQueue',
      'GLUE2ComputingShareMaxWallTime','GLUE2ComputingShareMaxCPUTime','GLUE2EntityOtherInfo'])[0][1]
    if 'GLUE2EntityOtherInfo' in res:
      for oi in res['GLUE2EntityOtherInfo']:
        if oi.startswith('CREAMCEId='):
          contact_str = oi[10:]
          break
  else:
    res = ldap_obj.search_s(dn, ldap.SCOPE_BASE, attrlist=['GLUE2ComputingShareMappingQueue',
      'GLUE2ComputingShareMaxWallTime','GLUE2ComputingShareMaxCPUTime'])[0][1]

  q_name = res['GLUE2ComputingShareMappingQueue'][0]
  #if 'GLUE2ComputingShareMaxWallTime' not in res and 'GLUE2ComputingShareMaxCPUTime' not in res:
  #  print "queue does not define walltime: %s" % dn

  max_wall = None
  max_cpu = None

  if 'GLUE2ComputingShareMaxWallTime' in res:
    max_wall = int(res['GLUE2ComputingShareMaxWallTime'][0])
  if 'GLUE2ComputingShareMaxCPUTime' in res:
    max_cpu = int(res['GLUE2ComputingShareMaxCPUTime'][0])

  if max_cpu is not None and (max_wall is None or max_cpu < max_wall):
    max_wall = max_cpu

  return (q_name, max_cpu, contact_str)

def get_glue2_jm(ldap_obj, dn):
  res = ldap_obj.search_s(dn, ldap.SCOPE_ONELEVEL, '(objectclass=GLUE2Manager)', attrlist=['GLUE2ManagerProductName'])
  if len(res) == 0:
    return None

  jm_res = res[0][1]['GLUE2ManagerProductName'][0]
  for jm in JM_REGEXES:
    if JM_REGEXES[jm].match(jm_res):
      jm_res = jm
      break

  return jm_res

def get_glue2_hosts(bdii_serv, base_dn='GLUE2GroupID=grid,o=glue'):
  l = ldap.open(bdii_serv, 2170)

  l.simple_bind_s('','')
  res = l.search_s(base_dn, ldap.SCOPE_SUBTREE, '(&(objectClass=GLUE2ComputingService)(|(GLUE2ServiceType=org.glite.ce.CREAM)(GLUE2ServiceType=org.nordugrid.arex)(GLUE2ServiceType=org.globus.gram)))',attrlist=['GLUE2ServiceID','GLUE2ServiceType'])

  hosts = {}
  for r in res:
    dn = r[0]
    vo_mappings = get_glue2_vo_mappings(l, dn)
    if len(vo_mappings) == 0:
      continue

    site_name = dn.split('GLUE2DomainID=')[1].split(',')[0]

    jm = get_glue2_jm(l, dn)
    #if jm is None:
    #  print "resource does not define jm: %s" % dn

    serv_type = r[1]['GLUE2ServiceType'][0]
    if serv_type == 'org.glite.ce.CREAM':
      gt = 'cream'
    elif serv_type == 'org.nordugrid.arex':
      gt = 'nordugrid'
    else:
      gt = 'gt5'

    queues = {}
    for vo_map in vo_mappings:
      dn_arr = vo_map[0].split(',')
      share_dn = ','.join(dn_arr[1:])
      q_name, max_wall, contact_str = get_glue2_q_attrs(l, share_dn, gt)
      if q_name not in queues:
        if contact_str is not None:
          queues[q_name] = {'max_walltime': max_wall, 'vos': set(), 'info_ref': share_dn, 'contact_str': contact_str}
        else:
          queues[q_name] = {'max_walltime': max_wall, 'vos': set(), 'info_ref': share_dn}

      queues[q_name]['vos'] |= vo_map[1]

    hosts[get_glue2_hostname(r[1]['GLUE2ServiceID'][0],r[1]['GLUE2ServiceType'][0])] = {'queues': queues,
      'gridtype': gt, 'job_manager': jm, 'site_name': site_name, 'info_type': 'BDII', 'info_server': bdii_serv}

  l.unbind()
  return hosts

def get_glue1_hosts(bdii_serv, base_dn='Mds-Vo-name=local,o=grid'):
  l = ldap.open(bdii_serv, 2170)

  l.simple_bind_s('','')
  res = l.search_s(base_dn, ldap.SCOPE_SUBTREE, '(&(objectClass=gluece)(|(GlueCEImplementationName=cream)(GlueCEImplementationName=arc-ce)(GlueCEImplementationName=globus)))', attrlist=['GlueCEAccessControlBaseRule','GlueCEInfoHostName','GlueCEName','GlueCEImplementationName','GlueCEInfoJobManager','GlueCEPolicyMaxWallClockTime','GlueCEPolicyMaxCPUTime'])

  l.unbind()

  hosts = {}
  for r in res:
    vos = set([])
    for rule in r[1]['GlueCEAccessControlBaseRule']:
      for vo in VO_REGEXES:
        if VO_REGEXES[vo].match(rule):
          vos.add(vo)
          break
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

      jm = r[1]['GlueCEInfoJobManager'][0]

      for jmr in JM_REGEXES:
        if JM_REGEXES[jmr].match(jm):
          jm = jmr
          break

      site_name = r[0].split('Mds-Vo-name=')[1].split(',')[0]

      hosts[host] = {'queues':{}, 'gridtype': gt, 'job_manager': jm, 'site_name': site_name, 'info_type': 'BDII',
        'info_server': bdii_serv}

    max_wall = None
    max_cpu = None

    # glue 1 has traditionally been in minutes so muliply by 60
    if 'GlueCEPolicyMaxWallClockTime' in r[1]:
      max_wall = int(r[1]['GlueCEPolicyMaxWallClockTime'][0]) * 60
    if 'GlueCEPolicyMaxCPUTime' in r[1]:
      max_cpu = int(r[1]['GlueCEPolicyMaxCPUTime'][0]) * 60

    if max_cpu is not None and (max_wall is None or max_cpu < max_wall):
      max_wall = max_cpu

    hosts[host]['queues'][r[1]['GlueCEName'][0]] = {'max_walltime': max_wall, 'vos': vos, 'info_ref': r[0]}

  return hosts

def get_osg_hosts(coll_serv):
  col = htcondor.Collector("%s:9619" % coll_serv)
  res = col.query(htcondor.AdTypes.Schedd, "true", ['Name','OSG_BatchSystems','OSG_ResourceGroup'])
  hosts = {}
  for r in res:
    if 'OSG_BatchSystems' in r:
      jm = r['OSG_BatchSystems']

      for jmr in JM_REGEXES:
        if JM_REGEXES[jmr].match(jm):
          jm = jmr
          break

    else:
      jm = None
    if 'OSG_ResourceGroup' in r:
      site_name = r['OSG_ResourceGroup']
    else:
      site_name = None
    hosts[r['Name']] = {'queues':{'default':{'info_ref':r['Name']}}, 'gridtype':'condor', 'job_manager': jm,
      'site_name': site_name, 'info_type': 'condor', 'info_server': coll_serv}

  return hosts
  
if __name__ == '__main__':
  # order matters. last queries overwrite previous ce info
  # so save most relevant calls for last
  hosts = get_glue1_hosts('exp-bdii.cern.ch')
  hosts.update(get_glue1_hosts('is.grid.iu.edu'))
  hosts.update(get_glue2_hosts('exp-bdii.cern.ch'))
  hosts.update(get_osg_hosts('collector.opensciencegrid.org'))

  #hosts = get_glue1_hosts('exp-bdii.cern.ch')
  #hosts = get_glue2_hosts('exp-bdii.cern.ch')
  #hosts = get_osg_hosts('collector.opensciencegrid.org')
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


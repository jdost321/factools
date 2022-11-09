#!/usr/bin/python3

import xml.parsers.expat
import time
import os
import ssl

from urllib.request import urlopen
from glideinwms.creation.lib import factoryXmlConfig

def get_dt_format(t_struct):
  return time.strftime("%Y-%m-%dT%H:%M:%S+00:00", t_struct)

downtimes = {}
entry_downtimes = {}
str_buf = []

###### OSG downtimes xml parsing variables and callbacks

# only collect downtimes if services are relevant
# 1 = CE
relevant_osg_services = set(['1'])

in_services = False

def osg_start_element(name, attrs):
  global cur_el
  global services
  global in_services
  global str_buf

  cur_el = name

  if name == 'Services':
    services = []
    in_services = True
  elif name == 'ResourceFQDN' or name == 'StartTime' or name == 'EndTime' or name == 'ID' or name == 'Description':
    str_buf = []
  
def osg_char_data(data):
  if cur_el == 'ResourceFQDN' or cur_el == 'StartTime' or cur_el == 'EndTime' or cur_el == 'ID' or cur_el == 'Description':
    str_buf.append(data)

def osg_end_element(name):
  global in_services
  global hostname
  global start_time
  global end_time
  global descript

  if name == 'Downtime':
    relevant = False
    for s in services:
      if s in relevant_osg_services:
        relevant = True
        break

    if relevant:
      if hostname not in downtimes:
        downtimes[hostname] = []
      downtimes[hostname].append({'start': start_time, 'end': end_time, 'desc': descript})

  elif name == 'ResourceFQDN':
    hostname = "".join(str_buf)
  elif name == 'StartTime':
    start_time = time.strptime("".join(str_buf), "%b %d, %Y %H:%M %p UTC")
      
  elif name == 'EndTime':
    end_time = time.strptime("".join(str_buf), "%b %d, %Y %H:%M %p UTC")

  elif name == 'ID' and in_services:
    services.append("".join(str_buf))
  elif name == 'Description' and not in_services:
    descript = "".join(str_buf)
  elif name == 'Services':
    in_services = False

###### END OSG downtimes xml parsing variables and callbacks

###### EGI downtimes xml parsing variables and callbacks

relevant_egi_services = set(['CREAM-CE','ARC-CE', 'org.opensciencegrid.htcondorce'])

def egi_start_element(name, attrs):
  global cur_el
  global str_buf

  cur_el = name

  if name == 'HOSTNAME' or name == 'START_DATE' or name == 'END_DATE' or name == 'DESCRIPTION' or name == 'SERVICE_TYPE' or name == 'SEVERITY':
    str_buf = []

def egi_char_data(data):
  if cur_el == 'HOSTNAME' or cur_el == 'START_DATE' or cur_el == 'END_DATE' or cur_el == 'DESCRIPTION' or cur_el == 'SERVICE_TYPE' or cur_el == 'SEVERITY':
    str_buf.append(data)

def egi_end_element(name):
  global hostname
  global start_time
  global end_time
  global descript
  global service
  global severity

  if name == 'DOWNTIME' and service in relevant_egi_services and severity == 'OUTAGE':
    if hostname not in downtimes:
      downtimes[hostname] = []
    downtimes[hostname].append({'start': start_time, 'end': end_time, 'desc': descript})
  elif name == 'HOSTNAME':
    hostname = "".join(str_buf)
  elif name == 'START_DATE':
    start_time = time.gmtime(float("".join(str_buf)))
  elif name == 'END_DATE':
    end_time = time.gmtime(float("".join(str_buf)))
  elif name == 'DESCRIPTION':
    descript = "".join(str_buf)
  elif name == 'SERVICE_TYPE':
    service = "".join(str_buf)
  elif name == 'SEVERITY':
    severity = "".join(str_buf)

###### END EGI downtimes xml parsing variables and callbacks

# Try GLIDEIN_FACTORY_DIR env var first
if 'GLIDEIN_FACTORY_DIR' in os.environ:
  gfactory_dir=os.environ['GLIDEIN_FACTORY_DIR']
# is it an rpm install?
elif os.path.isdir("/var/lib/gwms-factory/work-dir"):
  gfactory_dir="/var/lib/gwms-factory/work-dir"
else:
  gfactory_dir="."

url = 'https://topology.opensciencegrid.org/rgdowntime/xml'

dt_xml = urlopen(url)
#dt_xml = open("down.xml")

#for line in dt_xml:
#  print line,

#fout = open('osg_debug.xml','w')
#for line in dt_xml:
#  fout.write(line)

#fout.close()
#dt_xml.seek(0)

xmlparser = xml.parsers.expat.ParserCreate()
xmlparser.StartElementHandler = osg_start_element
xmlparser.EndElementHandler = osg_end_element
xmlparser.CharacterDataHandler = osg_char_data

xmlparser.ParseFile(dt_xml)

dt_xml.close()

egi_url = 'https://goc.egi.eu/gocdbpi/public/?method=get_downtime&ongoing_only=yes'

#dt_xml = open("egi_down.xml")
dt_xml = urlopen(egi_url, context=ssl._create_unverified_context())

xmlparser = xml.parsers.expat.ParserCreate()
xmlparser.StartElementHandler = egi_start_element
xmlparser.EndElementHandler = egi_end_element
xmlparser.CharacterDataHandler = egi_char_data

xmlparser.ParseFile(dt_xml)

dt_xml.close()

conf_path = "/etc/gwms-factory/glideinWMS.xml"
conf = factoryXmlConfig.parse(conf_path)

for entry in conf.get_child_list('entries'):
  if entry['enabled'] == 'True':
    if entry['gridtype'] == 'gt2' or entry['gridtype'] == 'gt5' or entry['gridtype'] == 'cream': 
      hostname = entry['gatekeeper'].split(':')[0]
    # works for nordugrid and condor-ce
    else:
      hostname = entry['gatekeeper'].split()[0]

    if hostname in downtimes:
      entry_downtimes[entry['name']] = downtimes[hostname]
      #for dt in downtimes[hostname]:
      #  print "%s %s %s All All # _ad_ %s" % (get_dt_format(dt['start']), get_dt_format(dt['end']), attrs['name'], ";".join(dt['desc'].split('\n')))

dt_file = open(os.path.join(gfactory_dir, "glideinWMS.downtimes"))
manual_dts = []

for line in dt_file:
  lines = line.split("#")

  # _force_ means don't consider for auto downtime at all
  # include in list of manual downtimes, and remove from aggregated list
  if '_force_' in lines[1]:
    manual_dts.append(line)
    entry = lines[0].split()[2]
    if entry in entry_downtimes:
      del entry_downtimes[entry]

  elif '_ad_' not in lines[1]:
    manual_dts.append(line)

dt_file.close()

new_dt_file = open(os.path.join(gfactory_dir, "glideinWMS.downtimes.tmp"), 'w')
for entry in sorted(entry_downtimes):
  for dt in entry_downtimes[entry]:
    new_dt_file.write("%s %s %s All All # _ad_ " % (get_dt_format(dt['start']), get_dt_format(dt['end']), entry))
    desc_str = ";".join(dt['desc'].split('\n'))
    try:
      new_dt_file.write("%s\n" % desc_str)
    except UnicodeEncodeError as ue:
      print("Unicode not allowed; skipping description for %s: %s" % (entry, ue))
      new_dt_file.write("\n")

for dt in manual_dts:
  new_dt_file.write(dt)

new_dt_file.close()

os.rename(os.path.join(gfactory_dir, "glideinWMS.downtimes.tmp"), os.path.join(gfactory_dir, "glideinWMS.downtimes"))

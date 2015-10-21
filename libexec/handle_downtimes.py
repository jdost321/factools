#!/usr/bin/python

import sys
import os
import time
import calendar
import xml.sax.saxutils
import xml.sax.xmlreader

DEL_T = 5 * 60
# truncate to scheduled interval in case
# there is a delay when this script is actually started
NOW = int(time.time()) / DEL_T * DEL_T

EMPTY_ATTRS = xml.sax.xmlreader.AttributesImpl({})

# get time since epoch in UTC assuming format like:
# 2012-10-18T12:49:27-07:00
def get_epoch(s):
  tz = int(s[-6:].split(':')[0]) * 3600
  return calendar.timegm(time.strptime(s[:-6], "%Y-%m-%dT%H:%M:%S")) - tz

def write_dt_end_item(xgen, entry, url, start, end, desc):
  xgen.characters(u"  ")
  xgen.startElement(u"item", EMPTY_ATTRS)

  xgen.characters(u"\n    ")
  xgen.startElement(u"title", EMPTY_ATTRS)
  xgen.characters(u"%s downtime ended" % entry)
  xgen.endElement(u"title")

  xgen.characters(u"\n    ")
  xgen.startElement(u"link", EMPTY_ATTRS)
  xgen.characters(url)
  xgen.endElement(u"link")

  xgen.characters(u"\n    ")
  xgen.startElement(u"description", EMPTY_ATTRS)
  xgen.characters(u'''
<table>
  <tr>
    <td><b>Entry:</b></td>
    <td>%s</td>
  </tr>
  <tr>
    <td><b>Start:</b></td>
    <td>%s</td>
  </tr>
  <tr>
    <td><b>End:</b></td>
    <td>%s</td>
  </tr>
</table>
<br />%s
    ''' % (entry,start,end,desc))
  xgen.endElement(u"description")

  xgen.characters(u"\n  ")
  xgen.endElement(u"item")
  xgen.characters(u"\n")

downtimes = []

if 'GLIDEIN_FACTORY_DIR' in os.environ:
  dt_file = open("%s/glideinWMS.downtimes" % os.environ['GLIDEIN_FACTORY_DIR'])
else:
  dt_file = open('/var/lib/gwms-factory/work-dir/glideinWMS.downtimes')

for line in dt_file:
  if line.startswith('#'):
    continue

  #start_time, end_time, entry = line.split()[:3]
  fields = line.split()
  if fields[1] == 'None':
    continue

  start_time = get_epoch(fields[0])
  end_time = get_epoch(fields[1])
  entry = fields[2]

  comment = line.split('#')[1].strip()

  #print "now:", NOW
  #print "start_time:", start_time
  #print "end_time:", end_time
  #print "next:", NOW + DEL_T

  if NOW >= start_time and NOW < end_time and NOW + DEL_T >= end_time:
    downtimes.append({'entry': unicode(entry), 'start': unicode(fields[0]),
      'end':unicode(fields[1]), 'comment':unicode(comment)})

dt_file.close()

if len(downtimes) == 0:
  sys.exit(0)

#for dt in downtimes:
#  print "%s: %s %s # %s" % (dt['entry'], dt['start'], dt['end'], dt['comment'])

if 'GLIDEIN_FACTORY_DIR' in os.environ:
  fout = open("%s/monitor/rss_downtimes.xml" % os.environ['GLIDEIN_FACTORY_DIR'], 'w')
else:
  fout = open('/var/lib/gwms-factory/work-dir/monitor/rss_downtimes.xml', 'w')

xgen = xml.sax.saxutils.XMLGenerator(fout, 'utf-8')

xgen.startDocument()

xgen.startElement(u"rss", xml.sax.xmlreader.AttributesImpl({u"version":u"2.0"}))

xgen.characters(u"\n")
xgen.startElement(u'channel', EMPTY_ATTRS)

xgen.characters(u"\n  ")
xgen.startElement(u"title", EMPTY_ATTRS)
xgen.characters(u'GlideinWMS Factory Downtimes Advertisements')
xgen.endElement(u"title")

xgen.characters(u"\n  ")
xgen.startElement(u"link", EMPTY_ATTRS)

if 'GLIDEIN_MON_URL' in os.environ:
  xgen.characters(u"%s/factoryStatusNow.html" % os.environ['GLIDEIN_MON_URL'])

xgen.endElement(u"link")

xgen.characters(u"\n  ")
xgen.startElement(u"description", EMPTY_ATTRS)
xgen.characters(u'Entry downtimes notifications')
xgen.endElement(u"description")
xgen.characters(u'\n')

for dt in downtimes:
  entry_stat_page=u''
  if 'GLIDEIN_MON_URL' in os.environ:
    entry_stats_page=u"%s/factoryEntryStatusNow.html?entry=%s" % (os.environ['GLIDEIN_MON_URL'], dt['entry'])
  else:
    entry_stats_page=u''

  write_dt_end_item(xgen, dt['entry'], entry_stats_page, dt['start'], dt['end'], dt['comment'])

xgen.endElement(u'channel')
xgen.characters(u'\n')
xgen.endElement(u"rss")
xgen.characters(u'\n')

xgen.endDocument()

fout.close()

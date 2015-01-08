#!/usr/bin/python

import time
import calendar

# get time since epoch in UTC assuming format like:
# 2012-10-18T12:49:27-07:00
def get_epoch(s):
  tz = int(s[-6:].split(':')[0]) * 3600
  return calendar.timegm(time.strptime(s[:-6], "%Y-%m-%dT%H:%M:%S")) - tz

dt = 5 * 60
# truncate to scheduled interval in case
# there is a delay when this script is actually started
now = int(time.time()) / dt * dt

dt_file = open("glideinWMS.downtimes")

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

  comment = line.split('#')[1]

  #print "now:", now
  #print "start_time:", start_time
  #print "end_time:", end_time
  #print "next:", now + dt

  if now >= start_time and now < end_time and now + dt >= end_time:
    print "%s: %s %s #%s" % (entry, start_time, end_time, comment),

dt_file.close()

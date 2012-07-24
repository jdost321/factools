#!/usr/bin/env python

import datetime
import sys

def calculateTime(s,e):
    sYear = datetime.date.today().year
    eYear = datetime.date.today().year
    sMonth = int(s.split()[2].split("/")[0])
    eMonth = int(e.split()[2].split("/")[0])
    #cornercase: start/end in different years
    if sMonth==12 and eMonth==01:
        sYear = datetime.date.today().year - 1
    sDay = int(s.split()[2].split("/")[1])
    eDay = int(e.split()[2].split("/")[1])
    sHour = int(s.split()[3].split(":")[0])
    eHour = int(e.split()[3].split(":")[0])
    sMinute = int(s.split()[3].split(":")[1])
    eMinute = int(e.split()[3].split(":")[1])
    sSecond = int(s.split()[3].split(":")[2])
    eSecond = int(e.split()[3].split(":")[2])
    start = datetime.datetime(sYear,sMonth,sDay,sHour,sMinute,sSecond)
    end = datetime.datetime(eYear,eMonth,eDay,eHour,eMinute,eSecond)
    return (end - start).seconds

#open file and read by line
# figure out how this command is going to be run, such as run it with one argument (location on condor activity log), run on all activity logs...
f = open(sys.argv[1])

#parse out the job ID and add it to a dict of form job:list of strings
d = {}
skipLine = False
for i in f:
    if i == "...\n":
        skipLine = False
        continue
    if skipLine:
        continue
    jobID = i.split("(")[1].split(")")[0]
    if jobID not in d:
        d[jobID] = [i]
    else:
        d[jobID].append(i)
    skipLine = True

#close file
f.close()

#increment through dict and calculate the run time of the glidein
for i in d.values():
    if len(i) > 4:
        start = end = None
        for j in i:
            if j[0:3] == "001":
                start = j
            elif j[0:3] == "005":
                end = j

        #print out the list of strings for any glideins running under 5 minutes (300 seconds)
        if start and end:
            if calculateTime(start,end) < 300:
                for j in i:
                    print j,
                print

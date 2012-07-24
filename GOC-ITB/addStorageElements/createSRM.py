#!/usr/bin/env python

import config
import elementtree.ElementTree as ET
import sys

#glideinWMSxml = ET.parse(config.locationGlideinWMSxml)
glideinWMSxml = ET.parse(sys.argv[1])
srmList = []
entries = glideinWMSxml.findall("entries/entry")
for entry in entries:
    if entry.get("enabled") == "True":
        lowerVOs = None
        baseVOs = None
        otherVOs = None
        otherSurls = []
        for attr in entry.findall("attrs/attr"):
            if attr.get("name") == "GLIDEIN_SEs":
                glideinSE = attr.get("value")
            elif attr.get("name") == "VOS_USING_SE_VONAME_LOWERCASE":
                lowerVOs = attr.get("value")
            elif attr.get("name") == "GLIDEIN_SE_VONAME_LOWERCASE":
                lowerSurl = attr.get("value")
            elif attr.get("name") == "VOS_USING_SE_BASEPATH":
                baseVOs = attr.get("value")
            elif attr.get("name") == "GLIDEIN_SE_BASEPATH":
                baseSurl = attr.get("value")
            elif attr.get("name") == "VOS_USING_SE_OTHER_SUBDIR":
                otherVOs = attr.get("value")
            elif "GLIDEIN_SE_PATH_" in attr.get("name"):
                otherSurls.append(attr.get("name").split("GLIDEIN_SE_PATH_")[1] + "\t" + attr.get("value"))
        if lowerVOs:
            for i in lowerVOs.split(","):
                srmList.append(glideinSE + "\t" + i + "\t" + lowerSurl + i.lower())
        if baseVOs:
            for i in baseVOs.split(","):
                srmList.append(glideinSE + "\t" + i + "\t" + baseSurl)
        if otherVOs:
            for i in otherSurls:
                srmList.append(glideinSE + "\t" + i)

for i in srmList:
    print i

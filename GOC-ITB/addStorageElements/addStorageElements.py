#!/bin/env python

import config
import elementtree.ElementTree as ET

def addElement(elementName,elementValue,elementParent):
    newElement = ET.SubElement(
        elementParent,"attr",
        name=elementName,
        const="True",
        glidein_publish="True",
        job_publish="True",
        parameter="True",
        publish="True",
        type="string",
        value=elementValue)

def checkForGlobalElements():
    attrNames = []
    for i in glideinWMSxml.find("attrs"):
        attrNames.append(i.get("name"))
    if "VOS_USING_SE_VONAME_LOWERCASE" not in attrNames:
        addElement("VOS_USING_SE_VONAME_LOWERCASE","",glideinWMSxml.find("attrs"))
    if "VOS_USING_SE_BASEPATH" not in attrNames:
        addElement("VOS_USING_SE_BASEPATH","",glideinWMSxml.find("attrs"))
    if "VOS_USING_SE_OTHER_SUBDIR" not in attrNames:
        addElement("VOS_USING_SE_OTHER_SUBDIR","",glideinWMSxml.find("attrs"))

def removeDuplicates(priority1vo,priority2vo,priority3vo,priority3surl):
    for i in priority3vo[:]:
        if i in priority1vo or i in priority2vo:
            priority3surl.pop(priority3vo.index(i))
            priority3vo.remove(i)
    for i in priority2vo[:]:
        if i in priority1vo:
            priority2vo.remove(i)
    for i in priority3vo[:]:
        if priority3vo.count(i) > 1:
            if i.lower() != priority3surl[priority3vo.index(i)].split("/")[-1].lower():
                priority3surl.pop(priority3vo.index(i))
                priority3vo.remove(i)

def removeElement(elementList,elementName,elementParent):
    for i in elementList:
        if elementName in i.get("name"):
            elementParent.remove(i)

surlFile = open(config.locationSurlFile)
surlLines = surlFile.readlines()
surlFile.close()

glideinWMSxml = ET.parse(config.locationGlideinWMSxml)

entries = glideinWMSxml.findall("entries/entry")

SEs = {}

mappedSVOs = {
    'ATLAS':'ATLAS',
    'CDFEMI':'CDF',
    'CMS':'CMS',
    'CMSHTPC':'CMS',
    'CMST2UCSD':'CMS',
    'EngageVO':'Engage',
    'EngageVOBigMem':'Engage',
    'EngageVOHTPC':'Engage',
    'EngageVOLong4d':'Engage',
    'EngageVOVirt':'Engage',
    'glowVO':'GLOW',
    'GLUEX':'Gluex',
    'HCC':'HCC',
    'HCC4d':'HCC',
    'HCCHTPC':'HCC',
    'HCCLONG':'HCC',
    'nanoHUB':'nanoHUB',
    'NEBioGrid':'SBGrid',
    'NEES':'NEES',
    'NWICG':'NWICG',
    'OSGVO':'OSG',
    'OSGVOHTPC':'OSG',
    'UCSDRok':'Engage'}

VOs = ['accelerator','alice','argoneut','atlas','belle','cdf','cdms','cigi',
    'cms','compbiogrid','csiu','dayabay','des','dosar','dream','dzero',
    'engage','enmr.eu','fermirrid','fermilab','fermilablbne','fermitest',
    'gcedu','gcvo','geant4','glow','gluex','gm2','gpn','gridunesp','grow',
    'hcc','i2u2','icecube','ilc','lbne','ligo','map','mars','microboobe',
    'minerva','miniboone','minos','mipp','mis','mu2e','nanohub','nebiogrid',
    'nees','nersc','nova','numi','nwicg','nysgrid','ops','osg','osgedu',
    'patriot','sbgrid','star','superbvo.org','suragrid','theory']

checkForGlobalElements()

for i in entries:
    if i.get("enabled") == "True":
        attrs = i.findall("attrs/attr")
        doEdit = None
        for j in attrs:
            if j.get("name") == "GLIDEIN_SEs":
                SE = j.get("value")
                doEdit = j
            if j.get("name") == "GLIDEIN_Supported_VOs":
                sVOs = j.get("value")

        #skipped unless GLIDEIN_SEs is defined
        if doEdit != None:
            translatedSVOs = []
            #translates VO list into a more generic VO list
            for j in sVOs.split(','):
                if j in mappedSVOs and mappedSVOs[j] not in translatedSVOs:
                    translatedSVOs.append(mappedSVOs[j])

            lowerVOs = []
            lowerSurls = ''
            baseVOs = []
            baseSurls = ''
            otherVOs = []
            otherSurls = []

            surlLines[0]

            #parsing through surl file to find a match
            for j in surlLines:
                line = j.split()
                if line[0] == SE and line[1] in translatedSVOs:
                    temp = line[2].split('/')
                    #lowercase check
                    if temp[-2] == line[1].lower():
                        lowerVOs.append(line[1])
                        if lowerSurls == '':
                            lowerSurls = "/".join(temp[0:-2])+"/"
                    #base check
                    elif temp[-2].lower() not in VOs:
                        baseVOs.append(line[1])
                        if baseSurls == '':
                            baseSurls = "/".join(temp[0:-1])+"/"
                    #other vos storage
                    else:
                        otherVOs.append(line[1])
                        otherSurls.append("/".join(temp[0:-1])+"/")

            removeDuplicates(lowerVOs,baseVOs,otherVOs,otherSurls)

            removeElement(attrs,"_SE_",i.find("attrs"))

            #adds SE location attribute to entry
            if len(lowerVOs) > 0:
                addElement("VOS_USING_SE_VONAME_LOWERCASE",",".join(lowerVOs),i.find("attrs"))
                addElement("GLIDEIN_SE_VONAME_LOWERCASE",lowerSurls,i.find("attrs"))
            if len(baseVOs) > 0:
                addElement("VOS_USING_SE_BASEPATH",",".join(baseVOs),i.find("attrs"))
                addElement("GLIDEIN_SE_BASEPATH",baseSurls,i.find("attrs"))
            if len(otherVOs) > 0:
                addElement("VOS_USING_SE_OTHER_SUBDIR",",".join(otherVOs),i.find("attrs"))
            for j in range(len(otherSurls)):
                addElement("GLIDEIN_SE_PATH_"+otherVOs[j],otherSurls[j],i.find("attrs"))

glideinWMSxml.write("glideinWMS.xml.new")

#!/usr/bin/env python

import config
#import elementtree.ElementTree as ET
import os
import sys

STARTUP_DIR="/home/gfactory/glideinWMS/creation"
sys.path.append(os.path.join(STARTUP_DIR,"lib"))
sys.path.append(os.path.join(STARTUP_DIR,"../lib"))
import cgWParams
#import ldapMonitor
import xmlParse

############# need to delete later
def addElement(elementParent,elementName,elementValue):
#    params.data["entries"][elementParent]["attrs"][u"%s"%elementName]=xmlParse.OrderedDict({

    elementParent[u"%s"%elementName]=xmlParse.OrderedDict({
        "comment": None,
        u"const": u"True",
        u"parameter": u"True",
        u"glidein_publish": u"True",
        u"value": u"%s"%elementValue,
        u"publish": u"True",
        u"job_publish": u"True",
        u"type": u"string"})

#    newElement = ET.SubElement(
#        elementParent,"attr",
#        name=elementName,
#        const="True",
#        glidein_publish="True",
#        job_publish="True",
#        parameter="True",
#        publish="True",
#        type="string",
#        value=elementValue)

############# need to delete later
def checkForGlobalElements():
    if "VOS_USING_SE_VONAME_LOWERCASE" not in params.attrs.keys():
        addElement(params.data["attrs"],"VOS_USING_SE_VONAME_LOWERCASE","")
    if "VOS_USING_SE_BASEPATH" not in params.attrs.keys():
        addElement(params.data["attrs"],"VOS_USING_SE_BASEPATH","")
    if "VOS_USING_SE_OTHER_SUBDIR" not in params.attrs.keys():
        addElement(params.data["attrs"],"VOS_USING_SE_OTHER_SUBDIR","")

def createGenericSupportedVOList(supportedVOs):
    mappedSupportedVOs = {
        "ATLAS":"ATLAS",
        "CDFEMI":"CDF",
        "CMS":"CMS",
        "CMSHTPC":"CMS",
        "CMST1":"CMS",
        "CMST2UCSD":"CMS",
        "EngageVO":"Engage",
        "EngageVOBigMem":"Engage",
        "EngageVOHTPC":"Engage",
        "EngageVOLong4d":"Engage",
        "EngageVOVirt":"Engage",
        "GLUEX":"Gluex",
        "glowVO":"GLOW",
        "HCC":"HCC",
        "HCC4d":"HCC",
        "HCCHTPC":"HCC",
        "HCCLONG":"HCC",
        "nanoHUB":"nanoHUB",
        "NEBioGrid":"SBGrid",
        "NEES":"NEES",
        "NWICG":"NWICG",
        "OSGVO":"OSG",
        "OSGVOHTPC":"OSG",
        "OSGVO_ITB":"OSG",
        "UCSDRok":"Engage"}
    genericSupportedVOs = []
    for i in supportedVOs.split(","):
        if i in mappedSupportedVOs:
            genericSupportedVOs.append(mappedSupportedVOs[i])
        else:
            print "  Add support in mappedSVOs for " + i
    return list(set(genericSupportedVOs))

def createSurlDictionary():
    surlDict = {}
    f = open(config.locationSurlFile)
    for i in f:
        #check for empty lines
        if len(i) < 5:
            continue
        ce = i.split()[0]
        vo = i.split()[1]
        surl = "/".join(i.split()[2].split("/")[:-1])
        if surl[-1] != "/":
            surl = surl + "/"
        if ce in surlDict:
            surlDict[ce] = surlDict[ce] + [vo + " " + surl]
        else:
            surlDict[ce] = [vo + " " + surl]
    f.close()
    return surlDict

############## need to delete later
#def parseSurl():
#    surlFile = open(config.locationSurlFile)
#    surlLines = surlFile.readlines()
#    surlFile.close()
#
############### need to delete later
#def removeDuplicates(priority1vo,priority2vo,priority3vo,priority3surl):
#    for i in priority3vo[:]:
#        if i in priority1vo or i in priority2vo:
#            priority3surl.pop(priority3vo.index(i))
#            priority3vo.remove(i)
#    for i in priority2vo[:]:
#        if i in priority1vo:
#            priority2vo.remove(i)
#    for i in priority3vo[:]:
#        if priority3vo.count(i) > 1:
#            if i.lower() != priority3surl[priority3vo.index(i)].split("/")[-1].lower():
#                priority3surl.pop(priority3vo.index(i))
#                priority3vo.remove(i)
#
############### need to delete later
def removeElement(elementList,elementName,elementParent):
    for i in elementList:
        if elementName in i.get("name"):
            elementParent.remove(i)

#remove all references to GLIDEIN_SE_ and VOS_USING_SE_ in case the SE URL is removed
def removeAllSURLAttributes(file):
    f = open(file)
    t = open("tempConfigFile", "w")
    for i in f:
        if "GLIDEIN_SE_" not in i and "VOS_USING_SE_" not in i:
            t.write(i)
    t.close()
    f.close()
    os.rename("tempConfigFile", file)


############################################################
#
# S T A R T U P
# 
############################################################

if __name__ == "__main__":

    removeAllSURLAttributes(config.locationGlideinWMSxml)

    surlDict = createSurlDictionary()
#    print surlDict

    params = cgWParams.GlideinParams("ZZZ",os.path.join(STARTUP_DIR,"web_base"),["ZZZ",config.locationGlideinWMSxml])

    checkForGlobalElements()

    for i in params.entries.keys():
        #remove all references to this tool in glideinWMS.xml
#        removeElement(attrs,"_SE_",i.find("attrs"))
        #increment through entries with GLIDEIN_SEs defined
        if params.entries[i]["enabled"]=="True" and params.entries[i]["attrs"].has_key("GLIDEIN_SEs"):
#            print i, params.entries[i]["enabled"], params.entries[i]["attrs"].has_key("GLIDEIN_SEs")
            currentGlideinSE = params.entries[i]["attrs"]["GLIDEIN_SEs"]["value"]
            currentGlideinSVOs = params.entries[i]["attrs"]["GLIDEIN_Supported_VOs"]["value"]
#            print params.entries[i]["attrs"]["GLIDEIN_SEs"]["value"]
#            print "currentGlideinSE in surlDict: " + currentGlideinSE in surlDict
#            print currentGlideinSE
#            print surlDict
            #check if this entries' GLIDEIN_SE is in the provided surl list
            if currentGlideinSE in surlDict:
                lowerVOs = []
                lowerSurl = ""
                baseVOs = []
                baseSurl = ""
                otherVOs = []
                otherSurls = []
                #translate glideinWMS.xml's GLIDEIN_Supported_VOs list to a more generic list
                print i
                genericSupportedVOs = createGenericSupportedVOList(currentGlideinSVOs)
#                print surlDict[params.entries[i]["attrs"]["GLIDEIN_SEs"]["value"]]
                #base case has to be the first check
                if len(currentGlideinSE) == 1:
                    vo = surlDict[currentGlideinSE].split()[0]
                    surl = surlDict[currentGlideinSE].split()[1]
                    if vo in genericSupportedVOs:
                        baseVOs.append(vo)
                        baseSurl = surl
                else:
                    voList = []
                    surlList = []
                    for j in surlDict[currentGlideinSE]:
                        vo = j.split()[0]
                        surl = j.split()[1]
                        if vo in genericSupportedVOs:
                            voList.append(vo)
                            surlList.append(surl)
                    #true = base case, false = lower or other case
                    if len(set(surlList)) == 1:
                        baseVOs = voList
                        baseSurl = surlList[0]
                    else:
                        #increment through list of surl's for that entry
                        for j in surlDict[currentGlideinSE]:
#                    print j
                            vo = j.split()[0]
#                    print vo
                            surl = j.split()[1]
#                    print surl
                            #checks if vo is in GLIDEIN_Supported_VOs
                            if vo in genericSupportedVOs:
                                #true = lower case, false = other case
#                        print vo.lower()
#                        print surl
#                        print surl.split("/")[-1].lower()
                                if vo.lower() == surl.split("/")[-2]:
                                    lowerVOs.append(vo)
                                    lowerSurl = surl.split(vo.lower())[0]
                                    #handles the case where there are multiple surls for a vo
                                    if vo in otherVOs:
                                        otherSurls.remove(otherSurls[otherVOs.index(vo)])
                                        otherVOs.remove(vo)
#                            print surl + " --> " + lowerSurls
                                elif vo not in lowerVOs:
                                    #handles the case where there are multiple surls for a vo
                                    if vo in otherVOs:
                                        if vo.lower() == surl.split("/")[-2].lower():
                                            otherSurls[otherVOs.index(vo)] = surl
                                    else:
                                        otherVOs.append(vo)
                                        otherSurls.append(surl)
#remove duplicates

#                print "@@@@@@@@@@@@@@@@@@@@"
#                print params.entries[i]["attrs"]["GLIDEIN_SEs"]["value"]
#                print lowerSurl, lowerVOs
#                print baseSurl, baseVOs
#                print otherSurls, otherVOs
#                print "@@@@@@@@@@@@@@@@@@@@"

                #adds SE location attribute to entry
                if len(lowerVOs) > 0:
                    addElement(params.data["entries"][i]["attrs"],"VOS_USING_SE_VONAME_LOWERCASE",",".join(lowerVOs))
                    addElement(params.data["entries"][i]["attrs"],"GLIDEIN_SE_VONAME_LOWERCASE",lowerSurl)
                if len(baseVOs) > 0:
                    addElement(params.data["entries"][i]["attrs"],"VOS_USING_SE_BASEPATH",",".join(baseVOs))
                    addElement(params.data["entries"][i]["attrs"],"GLIDEIN_SE_BASEPATH",baseSurl)
                if len(otherVOs) > 0:
                    addElement(params.data["entries"][i]["attrs"],"VOS_USING_SE_OTHER_SUBDIR",",".join(otherVOs))
                for j in range(len(otherSurls)):
                    addElement(params.data["entries"][i]["attrs"],"GLIDEIN_SE_PATH_"+otherVOs[j],otherSurls[j])

    params.save_into_file("glideinWMS.xml.new")

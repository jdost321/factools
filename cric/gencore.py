import json
import yaml
import pprint

#https://cms-cric.cern.ch/api/core/ce/query/?json
sites = json.load(open("core.json"))

result = {}

flavour_map = {
    "CREAM-CE" : "cream",
    "ARC-CE" : "nordugrid",
    "HTCONDOR-CE" : "condor"
}

for site, cel in sites.items(): # cel = ce list
#    import pdb;pdb.set_trace()
#    print site
    result[site] = {}
    result[site]["attrs"] = {} 
    for ce in cel:
        if ce["flavour"] == "CREAM-CE":
            continue
        print "****", ce["endpoint"]
#        result[site]["enabled"] = "True"
        result[site]["gatekeeper"] = ce["endpoint"]
        result[site]["gridtype"] = flavour_map[ce["flavour"]]
        result[site]["attrs"]["GLIDIEN_ResourceName"] = site
#        result[site]["GLIDEIN_Supported_VOs"] = "CMS"

with open("1category.yml", "w") as outfile:
    yaml.safe_dump(result, outfile, default_flow_style=False)

pprint.pprint(result)
print len(result)

"""
        for queue, _ in ce["queues"].items():
            print "********", queue
        if len(site["queues"]) == 1:
            q = site[""].values()[0]
        elif 'default' in  site['queues']:
            q = site[""]["default"]
        elif 'cms' in  site['queues']:
            q = site[""]["cms"]
        else:
            print "Skipping %s because it has %s queues and I cannot tell wihch one to use" % (site["name"], len(site["queues"]))
            return
"""

        # Queue (not for condor)
        # Max walltime
        # GLIDIEN_ResourceName (the name)
        # GLIDEIN_Supported_VOs (did not find it in the CRIC api)
        # result[site][""] = ""

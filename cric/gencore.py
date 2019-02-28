from __future__ import division
from __future__ import print_function

import sys
import json
import yaml
import pprint
import requests


url = "https://papa-cric.cern.ch/api/core/ce/query/?json"
response = requests.get(url)
if response.status_code != 200:
    print("ERROR. Can not get information from CRIC (%s)" % url)
    sys.exit(-1)
sites = response.json()

#https://cms-cric.cern.ch/api/core/ce/query/?json
#sites = json.load(open("core.json"))

result = {}

flavour_map = {
    "CREAM-CE" : "cream",
    "ARC-CE" : "nordugrid",
    "HTCONDOR-CE" : "condor"
}

for site, cel in sites.items(): # cel = ce list
    result[site] = {}
    for ce in cel:
        if ce["flavour"] == "CREAM-CE":
            continue
        gatekeeper = ce["endpoint"]
        result[site][gatekeeper] = {}
        result[site][gatekeeper]["gridtype"] = flavour_map[ce["flavour"]]
        result[site][gatekeeper]["attrs"] = {}
        result[site][gatekeeper]["attrs"]["GLIDIEN_ResourceName"] = { "value" : site }
        result[site][gatekeeper]["attrs"]["GLIDIEN_Country"] = { "value" : ce["country_code"] }

with open("1category.yml", "w") as outfile:
    yaml.safe_dump(result, outfile, default_flow_style=False)

pprint.pprint(result)
print(len(result))

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

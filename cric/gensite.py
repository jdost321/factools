from __future__ import division
from __future__ import print_function

import sys
import json
import yaml
import pprint
import requests


url = "https://papa-cric.cern.ch/api/cms/computeunit/query/?json"
response = requests.get(url)
if response.status_code != 200:
    print("ERROR. Can not get information from CRIC (%s)" % url)
    sys.exit(-1)
sites = response.json()

result = {}

for _, siteinfo in sites.items():
    site = siteinfo["rebus-site"]["name"]
    if site not in result:
        result[site] = {}
    for entry in siteinfo["glideinentries"]:
        grid_type = entry["gridtype"]
        if grid_type == "cream":
            continue
        glidein_cpus = entry["GLIDEIN_CPUS"]
        glidein_max_mem = entry["GLIDEIN_MaxMemMBs"]
        gatekeeper = entry["gatekeeper"]
        if " " in gatekeeper:
            gatekeeper = gatekeeper.split(" ")[1]
        if gatekeeper in result[site]:
            entry_number = max(result[site][gatekeeper], key=int) + 1
        else:
            result[site][gatekeeper] = {}
            entry_number = 1
        result[site][gatekeeper][entry_number] = {}
        result[site][gatekeeper][entry_number]["work_dir"] = entry["workdir"]
        result[site][gatekeeper][entry_number]["attrs"] = {}
        result[site][gatekeeper][entry_number]["attrs"]["GLIDEIN_REQUIRED_OS"] = { "value" : entry["GLIDEIN_REQUIRED_OS"]}
        result[site][gatekeeper][entry_number]["attrs"]["GLIDEIN_CPUS"] = { "value" : glidein_cpus}
        result[site][gatekeeper][entry_number]["attrs"]["GLIDEIN_MaxMemMBs"] = { "value" : glidein_max_mem}
        # Category 3 
        result[site][gatekeeper][entry_number]["rsl"] = entry["rsl"]
        result[site][gatekeeper][entry_number]["attrs"]["GLIDEIN_CMSSite"] = { "value" : entry["GLIDEIN_CMSSite"]}
        result[site][gatekeeper][entry_number]["attrs"]["GLIDEIN_Site"] = { "value" : site }

        try:
            if grid_type == "condor" and int(glidein_cpus) > 1:
                result[site][gatekeeper][entry_number]["submit_attrs"] = {}
                result[site][gatekeeper][entry_number]["submit_attrs"]["+maxMemory"] = glidein_max_mem
                result[site][gatekeeper][entry_number]["submit_attrs"]["+xcount"] = glidein_cpus
        except ValueError:
            pass

with open("2category.yml", "w") as outfile:
    yaml.safe_dump(result, outfile, default_flow_style=False)

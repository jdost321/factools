from __future__ import division
from __future__ import print_function

import sys
import json
import yaml
import requests

# Get information from CRIC
url = "https://papa-cric.cern.ch/api/core/ce/query/?json"
response = requests.get(url)
if response.status_code != 200:
    print("ERROR. Can not get information from CRIC (%s)" % url)
    sys.exit(-1)
sites = response.json()

# Map flavour with gridtype
flavour_map = {
    "CREAM-CE": "cream",
    "ARC-CE": "nordugrid",
    "HTCONDOR-CE": "condor"
}

# Collect necessary information
result = {}
for site, ce_list in sites.items():
    result[site] = {}
    for ce in ce_list:
        if ce["flavour"] == "CREAM-CE":
            continue
        gatekeeper = ce["endpoint"]
        result[site][gatekeeper] = {}
        result[site][gatekeeper]["DEFAULT_ENTRY"] = {}
        result[site][gatekeeper]["DEFAULT_ENTRY"]["gridtype"] = flavour_map[ce["flavour"]]
        result[site][gatekeeper]["DEFAULT_ENTRY"]["attrs"] = {}
        result[site][gatekeeper]["DEFAULT_ENTRY"]["attrs"]["GLIDEIN_Country"] = {"value": ce["country_code"]}
        result[site][gatekeeper]["DEFAULT_ENTRY"]["attrs"]["GLIDEIN_ResourceName"] = {"value": site}

# Write collected information to file
with open("1category.yml", "w") as outfile:
    yaml.safe_dump(result, outfile, default_flow_style=False)


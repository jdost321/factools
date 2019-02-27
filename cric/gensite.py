import sys
import json
import yaml
import pprint
import requests


url = "https://papa-cric.cern.ch/api/cms/computeunit/query/?json"
response = requests.get(url)
if response.status_code != 200:
    print "ERROR. Can not get information from CRIC (%s)" % url
    sys.exit(-1)
sites = response.json()

#https://cms-cric.cern.ch/api/cms/computeunit/query/?json
#sites = json.load(open("admin.json"))

result = {}

for _, siteinfo in sites.items():
    site = siteinfo["rebus-site"]["name"]
    if site not in result:
        result[site] = {}
    for entry in siteinfo["glideinentries"]:
        if entry["gridtype"] == "cream":
            continue
        gatekeeper = entry["gatekeeper"]
        if " " in gatekeeper:
            gatekeeper = gatekeeper.split(" ")[1]
        result[site][gatekeeper] = {}
        result[site][gatekeeper]["work_dir"] = entry["workdir"]
        result[site][gatekeeper]["attrs"] = {}
        result[site][gatekeeper]["attrs"]["GLIDEIN_REQUIRED_OS"] = entry["GLIDEIN_REQUIRED_OS"]
        result[site][gatekeeper]["attrs"]["GLIDEIN_CPUS"] = entry["GLIDEIN_CPUS"]
        result[site][gatekeeper]["attrs"]["GLIDEIN_MaxMemMBs"] = entry["GLIDEIN_MaxMemMBs"] or 2500
        # Category 4
        result[site][gatekeeper]["rsl"] = entry["rsl"]
        result[site][gatekeeper]["attrs"]["GLIDEIN_CMSSite"] = entry["GLIDEIN_CMSSite"]
        result[site][gatekeeper]["attrs"]["GLIDEIN_Site"] = site
#        result[site][gatekeeper]["attrs"]["GLIDEIN_Supported_VOs"] = "CMS"
#        result[site][gatekeeper]["trust_domain"] = "grid"

with open("2category.yml", "w") as outfile:
    yaml.safe_dump(result, outfile, default_flow_style=False)

pprint.pprint(result)
print len(result)

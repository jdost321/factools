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
        result[site][gatekeeper] = {}
        result[site][gatekeeper]["work_dir"] = entry["workdir"]
        result[site][gatekeeper]["attrs"] = {}
        result[site][gatekeeper]["attrs"]["GLIDEIN_REQUIRED_OS"] = entry["GLIDEIN_REQUIRED_OS"]
        result[site][gatekeeper]["attrs"]["GLIDEIN_CPUS"] = glidein_cpus
        result[site][gatekeeper]["attrs"]["GLIDEIN_MaxMemMBs"] = glidein_max_mem
        result[site][gatekeeper]["rsl"] = entry["rsl"]
        result[site][gatekeeper]["attrs"]["GLIDEIN_CMSSite"] = entry["GLIDEIN_CMSSite"]
        result[site][gatekeeper]["attrs"]["GLIDEIN_Site"] = site
        try:
            if grid_type == "condor" and int(glidein_cpus) > 1:
                result[site][gatekeeper]["submit_attrs"] = {}
                result[site][gatekeeper]["submit_attrs"]["+maxMemory"] = glidein_max_mem
                result[site][gatekeeper]["submit_attrs"]["+xcount"] = glidein_cpus
        except ValueError:
            pass

with open("2category.yml", "w") as outfile:
    yaml.safe_dump(result, outfile, default_flow_style=False)

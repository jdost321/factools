from __future__ import division
from __future__ import print_function


import sys
import json
import yaml
import logging
import requests

from utils import CRIC_CORE, CRIC_CMS, CRIC_CMS_LINK, CRIC_CORE_LINK
 

# Get information from CRIC
def get_information(url):
    response = requests.get(url)
    if response.status_code != 200:
        print("ERROR. Can not get information from CRIC (%s)" % url)
        sys.exit(-1)

    return response.json()


# Select necessary information for core
def select_core_information(sites):
    flavour_map = {
        "CREAM-CE": "cream",
        "ARC-CE": "nordugrid",
        "HTCONDOR-CE": "condor"
    }
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

    return result


# Select necessary information for entries
def select_entries_information(sites, production):
    result = {}
    for cu, site_info in sites.items():
        logging.debug("Processing %s", cu)
        site = site_info["rebus-site"]["name"]
        if site not in result:
            result[site] = {}
        for entry in site_info["glideinentries"]:
            logging.debug("  processing %s", entry)
            if production and entry["queue_status"] != "Production":
                continue
            grid_type = entry["gridtype"]
            if grid_type == "cream":
                logging.debug("Skipping cream ce")
                continue
            glidein_cpus = entry["GLIDEIN_CPUS"]
            glidein_max_mem = entry["GLIDEIN_MaxMemMBs"]
            gatekeeper = entry["gatekeeper"]
            glidein_cms_site= entry["GLIDEIN_CMSSite"]
            if grid_type == "condor":
                gatekeeper = gatekeeper.split(" ")[1]
            if gatekeeper in result[site]:
                last_entry_name = result[site][gatekeeper].keys()[-1]
                last_entry_name_parts_list = last_entry_name.split("_")
                try:
                    entry_name = "_".join(last_entry_name_parts_list[:-1]) + "_" + str(int(last_entry_name_parts_list[-1]) + 1)
                except ValueError:
                    entry_name = last_entry_name + "_2"
            else:
                result[site][gatekeeper] = {}
                entry_name = "CMSHTPC_"
                try:
                    if int(glidein_cpus) == 1:
                        entry_name = "CMS_"
                except ValueError:
                    pass
                entry_name = entry_name + glidein_cms_site + "_" + gatekeeper.split(".")[0]
            result[site][gatekeeper][entry_name] = {}
            result[site][gatekeeper][entry_name]["rsl"] = entry["rsl"]
            result[site][gatekeeper][entry_name]["work_dir"] = entry["workdir"]
            result[site][gatekeeper][entry_name]["attrs"] = {}
            result[site][gatekeeper][entry_name]["attrs"]["GLIDEIN_CMSSite"] = {"value": glidein_cms_site}
            result[site][gatekeeper][entry_name]["attrs"]["GLIDEIN_CPUS"] = {"value": glidein_cpus}
            result[site][gatekeeper][entry_name]["attrs"]["GLIDEIN_MaxMemMBs"] = {"value": glidein_max_mem}
            result[site][gatekeeper][entry_name]["attrs"]["GLIDEIN_REQUIRED_OS"] = {"value": entry["GLIDEIN_REQUIRED_OS"]}
            result[site][gatekeeper][entry_name]["attrs"]["GLIDEIN_Site"] = {"value": site}
            try:
                if grid_type == "condor" and int(glidein_cpus) > 1:
                    result[site][gatekeeper][entry_name]["submit_attrs"] = {}
                    result[site][gatekeeper][entry_name]["submit_attrs"]["+maxMemory"] = glidein_max_mem
                    result[site][gatekeeper][entry_name]["submit_attrs"]["+xcount"] = glidein_cpus
            except ValueError:
                pass

    return result


# Write collected information to file
def write_to_file(file_name, information):
    with open(file_name, "w") as outfile:
        yaml.safe_dump(information, outfile, default_flow_style=False)


def set_logging():
    logging.basicConfig(filename='cric.log', filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

def main():
    set_logging()
    production = False
    if len(sys.argv) > 1:
        if sys.argv[1] == "--production":
            production = True
        else:
            print("Usage: generate.py [--production]")
            sys.exit(1)
    logging.info("Getting information from core cric")
    sites = get_information(CRIC_CORE_LINK)
    result = select_core_information(sites)
    write_to_file(CRIC_CORE, result)

    logging.info("Getting information from cms cric")
    sites = get_information(CRIC_CMS_LINK)
    result = select_entries_information(sites, production)
    write_to_file(CRIC_CMS, result)


if __name__ == "__main__":
    main()


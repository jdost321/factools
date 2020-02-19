import os
import sys
import yaml
import urllib2
import htcondor
import fractions
import xmltodict
import collections

from cfg.config import OSG_COLLECTOR, OSG_YAML, OSG_WHITELIST, OSG_DEFAULT
from libs.utils import entry_stub, GLIDEIN_Supported_VOs_map, default_attr, MergeError, get_attr_str, write_to_file, update, get_yaml_file_info, write_to_yaml_file, get_submit_attr_str, write_to_xml_file


def get_VOs(allowed_vos):
    """This function converts the list of VO from the collector to the frontend ones

    Args:
        allowed_vos (list): The list ov vos in the OSG collector

    Returns:
        set: The set of frontend VOs to add to the configuration GLIDEIN_SupportedVOs
    """
    VOs = set()
    for VO in allowed_vos:
        if VO in GLIDEIN_Supported_VOs_map:
            VOs.add(GLIDEIN_Supported_VOs_map[VO])
        else:
            print VO + " VO is not in GLIDEIN_Supported_VOs_map"

    return VOs


def get_information(host):
    """Query the OSG collector and get information about the known HTCondor-CE.

    The OSG collector is queried with the -sched option to get information about
    all the HTCondorCEs. The relevant OSG resource information is then organized
    in a dict.

    Args:
        host (str): The hostname where the OSG collector is running

    Returns:
        dict: A resource dictionary whose keys are the resources ('cedar', 'UCHICAGO', 'NMSU')
            and its values are the needed information to create the entry. For example:

            {'hosted-ce32.grid.uchicago.edu': {'DEFAULT_ENTRY': {'attrs': {'GLIDEIN_CPUS': {'value': 16L},
                                                                           'GLIDEIN_MaxMemMBs': {'value': 163840L},
                                                                           'GLIDEIN_Max_Walltime': {'value': 171000L},
                                                                           'GLIDEIN_ResourceName': {'value': 'NEMO'},
                                                                           'GLIDEIN_Site': {'value': 'OSG_US_UWM_NEMO'},
                                                                           'GLIDEIN_Supported_VOs': {'value': 'OSGVO'}},
                                                                 'gridtype': 'condor',
                                                                 'submit_attrs': {'+maxMemory': 163840L,
                                                                                  '+maxWallTime': 2880L,
                                                                                  '+xcount': 16L}}}}
    """
    collector = htcondor.Collector(host)
    ces = collector.query(htcondor.AdTypes.Schedd)
    result = {}
    entry = "DEFAULT_ENTRY"
    for ce in ces:
        # Only focus on the hsotedCEs for the time being
        if not ce["Name"].lower().startswith("hosted-ce"):
            continue
        if "OSG_ResourceGroup" in ce:
            site = ce["OSG_ResourceGroup"]
            if site:
                if site not in result:
                    result[site] = {}
                gatekeeper = ce["Name"].lower()
                result[site][gatekeeper] = {}
                resource = ""
                if "OSG_Resource" in ce:
                    resource = ce["OSG_Resource"]
                if "OSG_ResourceCatalog" in ce:
                    VOs = set()
                    memory = sys.maxint
                    walltime = sys.maxint
                    CPUs = "" 
                    for OSG_ResourceCatalog in ce["OSG_ResourceCatalog"]:
                        if "AllowedVOs" in OSG_ResourceCatalog:
                            if len(VOs) == 0:
                                VOs = get_VOs(OSG_ResourceCatalog["AllowedVOs"])
                            else:
                                VOs = VOs.intersection(get_VOs(OSG_ResourceCatalog["AllowedVOs"]))
                        if "Memory" in OSG_ResourceCatalog:
                            memory = min(memory, OSG_ResourceCatalog["Memory"])
                        if "MaxWallTime" in OSG_ResourceCatalog:
                            walltime = min(walltime, OSG_ResourceCatalog["MaxWallTime"])
                        if "CPUs" in OSG_ResourceCatalog:
                            if CPUs == "" :
                                CPUs = OSG_ResourceCatalog["CPUs"]
                            else:
                                CPUs = fractions.gcd(CPUs, OSG_ResourceCatalog["CPUs"])
                    result[site][gatekeeper][entry] = {}
                    result[site][gatekeeper][entry]["gridtype"] = "condor"
                    result[site][gatekeeper][entry]["attrs"] = {}
                    result[site][gatekeeper][entry]["attrs"]["GLIDEIN_Site"] = {"value": resource}
                    if resource:
                        result[site][gatekeeper][entry]["attrs"]["GLIDEIN_ResourceName"] = {"value": site}
                    if len(VOs) > 0:
                        result[site][gatekeeper][entry]["attrs"]["GLIDEIN_Supported_VOs"] = {"value": ",".join(VOs)}
                    else:
                        print gatekeeper + " CE does not have VOs"
                    result[site][gatekeeper][entry]["submit_attrs"] = {}
                    if CPUs != "":
                        result[site][gatekeeper][entry]["attrs"]["GLIDEIN_CPUS"] = {"value": CPUs}
                        result[site][gatekeeper][entry]["submit_attrs"]["+xcount"] = CPUs
                    if walltime != sys.maxint:
                        glide_walltime = walltime * 60 - 1800
                        result[site][gatekeeper][entry]["attrs"]["GLIDEIN_Max_Walltime"] = {"value": glide_walltime}
                        result[site][gatekeeper][entry]["submit_attrs"]["+maxWallTime"] = walltime
                    if memory != sys.maxint:
                        result[site][gatekeeper][entry]["attrs"]["GLIDEIN_MaxMemMBs"] = {"value": memory}
                        result[site][gatekeeper][entry]["submit_attrs"]["+maxMemory"] = memory
                else:
                    print gatekeeper + " CE does not have OSG_ResourceCatalog attribute"
            else:
                print gatekeeper + " CE does not have OSG_ResourceGroup attribute"

    return result


def get_entries_configuration(data):
    """Given the dictionary of resources, returns the generated factory xml file

    Args:
        data (dict): A dictionary similar to the one returned by ``get_information``

    Returns:
        str: The factory cml file as a string
    """
    entries_configuration = ""
    for site, site_information in data.items():
        for ce, ce_information in site_information.items():
            for entry, entry_information in ce_information.items():
                entry_configuration = entry_information
                entry_configuration["entry_name"] = entry
                entry_configuration["attrs"]["GLEXEC_BIN"] = {"value": "NONE"} # Can we get this information?
                entry_configuration["attrs"]["GLIDEIN_REQUIRED_OS"] = {"comment" : "This value has been hardcoded", "value": "any"} # Can we get this information?
                entry_configuration["gatekeeper"] = ce + " " + ce + ":9619" # Probably we can use port from attribute AddressV1 or CollectorHost
                entry_configuration["rsl"] = ""
                entry_configuration["attrs"] = get_attr_str(entry_configuration["attrs"])
                if  "submit_attrs" in entry_configuration:
                    entry_configuration["submit_attrs"] = get_submit_attr_str(entry_configuration["submit_attrs"])
                else:
                    entry_configuration["submit_attrs"] = ""
                entries_configuration += entry_stub % entry_configuration

    return entries_configuration
    

def merge_yaml():
    """Merges different yaml file and return the corresponding resource dictionary

    Three different yam files are merged. First we read the factory white list/override file that
    contains the list of entries operators want to generate, with the parameters they want to override.
    Then the yaml generated from the OSG collector and the default yam file are read.
    For each entry an all the operator information are "updated" with the information coming from the
    collector first, and from the default file next.

    Returns:
        dict: a dict similar to the one returned by ``get_information``, but with all the defaults and
            the operators overrides in place (only whitelisted entries are returned).
    """
    out = {}
    out = get_yaml_file_info(OSG_YAML, 5)
    OSG_information = get_yaml_file_info(OSG_WHITELIST, 6)
    default_information = get_yaml_file_info(OSG_DEFAULT, 7)
    for site, site_information in out.items():
        if site not in OSG_information:
            print("You put %s in the whitelist file, but the site is not present in the collector" % site)
            raise MergeError(8)
        for ce, ce_information in site_information.items():
            if ce not in OSG_information[site]:
                print ("Working on whitelisted site %s: cannot find ce %s in the generated OSG.yaml" % (site, ce))
                raise MergeError(9)
            for entry, entry_information in ce_information.items():
                if entry_information == None:
                    out[site][ce][entry] = OSG_information[site][ce]["DEFAULT_ENTRY"]
                    entry_information = out[site][ce][entry]
                else:
                    update(entry_information, OSG_information[site][ce]["DEFAULT_ENTRY"], overwrite=False)
                update(entry_information, default_information["DEFAULT_SITE"]["DEFAULT_GETEKEEPER"]["DEFAULT_ENTRY"], overwrite=False)

    return out


def main():
    """The main"""
    # Queries the OSG collector
    result = get_information(OSG_COLLECTOR)
    # Write the received information to the OSG.yml file
    write_to_yaml_file(OSG_YAML, result)
    # Merges different yaml files: the defaults, the generated one, and the factory overrides
    result = merge_yaml()
    # Convert the resoruce dictionary obtained this way into a string (xml)
    entries_configuration = get_entries_configuration(result)
    # Write the factory configuration file on the disk
    write_to_xml_file("entries.xml", entries_configuration)
    

if __name__ == "__main__":
    try:
        main()
    except MergeError as me:
        print("Error! " + MergeError.codes_map[me.code])
        sys.exit(me.code)

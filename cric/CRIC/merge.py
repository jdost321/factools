from __future__ import division
from __future__ import print_function


import os
import sys
import yaml
import collections

from utils import CRIC_CORE, CRIC_CMS, FACT_OVERRIDE, DEFAULT, entry_stub, default_attr, MergeError, get_attr_str, write_to_file, update, get_yaml_file_info, write_to_yaml_file


# Merge data from all yaml files
def merge_yaml():
    out = {}
    out = get_yaml_file_info(FACT_OVERRIDE, 3)
    gensites_info = get_yaml_file_info(CRIC_CMS, 2)
    gencore_info = get_yaml_file_info(CRIC_CORE, 1)
    defaults_info = get_yaml_file_info(DEFAULT, 4)

    for site, ce_list in out.items():
        for gatekeeper, ce_info in ce_list.items():
            for entry, entry_info in ce_info.items():
                if entry_info == None:
                    out[site][gatekeeper][entry] = gensites_info[site][gatekeeper][entry]
                    entry_info = out[site][gatekeeper][entry]
                else:
                    update(entry_info, gensites_info[site][gatekeeper][entry], overwrite=False)
                update(entry_info, gencore_info[site][gatekeeper]["DEFAULT_ENTRY"], overwrite=False)
                update(entry_info, defaults_info["DEFAULT_SITE"]["DEFAULT_GETEKEEPER"]["DEFAULT_ENTRY"], overwrite=False)

    return out


# Make dictionary to populate entry_stub variable
def get_dict(gatekeeper, entry, entry_info):
    out = {}
    out["gatekeeper"] = gatekeeper
    out["entry_name"] = entry
    out.update(entry_info)

    return out


# Collect all submit attributes
def get_submit_attr_str(submit_attrs):
    out = ""
    for name, value in sorted(submit_attrs.items()):
        out += '\n                  <submit_attr name="%s" value="%s"/>' % (name, value)

    return out


def main():
    out_conf = ""
    cfg_all = merge_yaml()
    for site, ce_list in cfg_all.items():
        for gatekeeper, ce_info in ce_list.items():
            for entry, entry_info in ce_info.items():
                conf_dict = get_dict(gatekeeper, entry, entry_info)
                conf_dict["attrs"] = get_attr_str(conf_dict["attrs"])
                if "submit_attrs" in conf_dict:
                    conf_dict["submit_attrs"] = get_submit_attr_str(conf_dict["submit_attrs"])
                else:
                    conf_dict["submit_attrs"] = ""
                if conf_dict["gridtype"] == "condor":
                    gatekeeper = conf_dict["gatekeeper"]
                    conf_dict["gatekeeper"] = gatekeeper + " " + gatekeeper + ":9619"
                if conf_dict["gridtype"] == "nordugrid":
                    conf_dict["rsl"] = ' rsl="' + conf_dict["rsl"] + '"'
                out_conf += entry_stub % conf_dict
    write_to_file("automatically_generated.xml", out_conf)


if __name__ == "__main__":
    try:
        main()
    except MergeError as me:
        print(MergeError.codes_map[me.code])
        sys.exit(me.code)


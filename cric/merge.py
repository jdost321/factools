from __future__ import division
from __future__ import print_function

import os
import sys
import glob
import json
import yaml
import collections

entry_stub = """      <entry name="%(entry_name)s" auth_method="grid_proxy" comment="Entry automatically generated" enabled="%(enabled)s" gatekeeper="%(gatekeeper)s" gridtype="%(gridtype)s"%(rsl)s proxy_url="OSG" trust_domain="grid" verbosity="std" work_dir="%(work_dir)s">
         <config>
            <max_jobs>
               <default_per_frontend glideins="5000" held="50" idle="100"/>
               <per_entry glideins="10000" held="1000" idle="4000"/>
               <per_frontends>
               </per_frontends>
            </max_jobs>
            <release max_per_cycle="20" sleep="0.2"/>
            <remove max_per_cycle="5" sleep="0.2"/>
            <restrictions require_glidein_glexec_use="False" require_voms_proxy="False"/>
            <submit cluster_size="10" max_per_cycle="25" sleep="2" slots_layout="fixed">
               <submit_attrs>
%(submit_attrs)s
               </submit_attrs>
            </submit>
         </config>
         <allow_frontends>
         </allow_frontends>
         <attrs>
%(attrs)s
         </attrs>
         <files>
         </files>
         <infosys_refs>
         </infosys_refs>
         <monitorgroups>
         </monitorgroups>
      </entry>
"""

class MergeError(Exception):
    """ Class to handle error in the merge script. Error codes:
    """
    codes_map = {
        1 : "default.yml file not found",
        2 : "1category.yml file not found",
    }

    def __init__(self, code):
        self.code = code

def update(d, u, overwrite=True):
    for k, v in u.items():
        if v == None:# and overwrite:
            if k in d:
                del d[k]
        elif isinstance(v, collections.Mapping):
            d[k] = update(d.get(k, {}), v, overwrite)
        else:
            if overwrite or k not in d:
                d[k] = v
    return d

def merge_yaml():
    out = {}
    for cfg in sorted(glob.glob("*.yml")):
        if cfg == "default.yml" or cfg == "1category.yml":
            continue
        with open(cfg) as fd:
            cfg_obj = yaml.load(fd)
            update(out, cfg_obj)

    if not os.path.isfile("1category.yml"):
        raise MergeError(2)
    with open("1category.yml") as fd:
        entries_defaults = yaml.load(fd)

    for site, cel in out.items():
        for gatekeeper, ceinfo in cel.items():
            for entry, entryinfo in ceinfo.items():
                update(entryinfo, entries_defaults[site][gatekeeper]["DEFAULT_ENTRY"])
                update(entryinfo["attrs"], entries_defaults[site][gatekeeper]["DEFAULT_ENTRY"]["attrs"])

    # Merging defaults (will use update with overwrite False)
    if not os.path.isfile("default.yml"):
        raise MergeError(1)
    with open("default.yml") as fd:
        defaults = yaml.load(fd)

    for site, cel in out.items():
        for gatekeeper, ceinfo in cel.items():
            for entry, entryinfo in ceinfo.items():
                update(entryinfo, defaults["DEFAULT_SITE"]["DEFAULT_GETEKEEPER"]["DEFAULT_ENTRY"], overwrite=False)
                update(entryinfo["attrs"], defaults["DEFAULT_SITE"]["DEFAULT_GETEKEEPER"]["DEFAULT_ENTRY"]["attrs"], 
                       overwrite=False)

    return out

def get_dict(site, gatekeeper, ceinfo, entry_number):
    out = {}
    out["gatekeeper"] = gatekeeper
    out.update(ceinfo)
    entry_name = "CMSHTPC_"
    try:
        if int(out["attrs"]["GLIDEIN_CPUS"]["value"]) == 1:
            entry_name = "CMS_"
    except ValueError:
        pass
    out['entry_name'] = entry_name + out["attrs"]["GLIDEIN_CMSSite"]["value"] + "_" + out["gatekeeper"].split('.')[0] + ("_" + str(entry_number) if entry_number > 1 else "")
    return out

def get_attr_str(attrs):
    out = ""
    for name, d in sorted(attrs.items()):
        d["name"] = name
        if "comment" not in d:
            d["comment"] = ""
        else:
            d["comment"] = " comment=\"" + d["comment"]  + "\""
        if "value" in d:
            out += '            <attr name="%(name)s"%(comment)s const="%(const)s" glidein_publish="%(glidein_publish)s" job_publish="%(job_publish)s" parameter="%(parameter)s" publish="%(publish)s" type="%(type)s" value="%(value)s"/>\n' % d
    return out[:-1]

def get_submit_attr_str(submit_attrs):
    out = ""
    for n, v in sorted(submit_attrs.items()):
        out += '                  <submit_attr name="%s" value="%s"/>\n' % (n, v)
    return out[:-1]

def main():
    out_conf = ""

    cfg_all = merge_yaml()
    for site, cel in cfg_all.items():
        for gatekeeper, ceinfo in cel.items():
            for entry, entryinfo in ceinfo.items():
                conf_dict = get_dict(site, gatekeeper, entryinfo, entry)
                conf_dict["attrs"] = get_attr_str(conf_dict["attrs"])
                conf_dict["submit_attrs"] = get_submit_attr_str(conf_dict["submit_attrs"])
                if conf_dict["gridtype"] == "condor":
                    gatekeeper = conf_dict["gatekeeper"]
                    conf_dict["gatekeeper"] = gatekeeper.split(":")[0] + " " + gatekeeper
                rsl = conf_dict["rsl"]
                if rsl != "":
                    conf_dict["rsl"] = " rsl=\"" + rsl + "\""
                out_conf += entry_stub % conf_dict
    print("<glidein>")
    print("   <entries>")
    print(out_conf[:-1])
    print("   </entries>")
    print("   <entry_sets>")
    print("   </entry_sets>")
    print("</glidein>")

if __name__ == "__main__":
    try:
        main()
    except MergeError as me:
        print(MergeError.codes_map[me.code])
        sys.exit(me.code)

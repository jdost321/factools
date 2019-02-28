from __future__ import division
from __future__ import print_function

import os
import sys
import glob
import json
import yaml
import collections

import pdb

entry_stub = """       <entry name="%(entry_name)s" auth_method="grid_proxy" comment="Entry automatically generated" enabled="%(enabled)s" gatekeeper="%(gatekeeper)s" gridtype="%(gridtype)s" rsl="%(rsl)s" proxy_url="OSG" trust_domain="grid" verbosity="std" work_dir="%(work_dir)s">
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
               <!--submit_attrs>(SUBMIT_ATTRS)s
               </submit_attrs-->
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
        1 : "default.yaml file not found",
    }

    def __init__(self, code):
        self.code = code

def update(d, u, overwrite=True):
    for k, v in u.items():
        if v == None:
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
        if cfg == "default.yml":
            raise MergeError(1)
        with open(cfg) as fd:
            cfg_obj = yaml.load(fd)
            update(out, cfg_obj)

    # Merging defaults (will use update with overwrite False)
    if not os.path.isfile("default.yml"):
        return out
    with open("default.yml") as fd:
        defaults = yaml.load(fd)

    for site, cel in out.items():
        for gatekeeper, ceinfo in cel.items():
            update(ceinfo, defaults['DEFAULT_SITE']['DEFAULT_GETEKEEPER'], overwrite=False)
            update(ceinfo['attrs'], defaults['DEFAULT_SITE']['DEFAULT_GETEKEEPER']['attrs'], 
                   overwrite=False)

    return out

def get_dict(site, gatekeeper, ceinfo):
    out = {}
    out["gatekeeper"] = gatekeeper
    out.update(ceinfo)
    out['entry_name'] = "CMS_" + site + "_" + out["attrs"]["GLIDEIN_CMSSite"] + "_" + out["gatekeeper"].split('.')[0]
    return out

def get_attr_str(attrs):
   out = ""
   for n, v in sorted(attrs.items()):
        out += '<attr name="%s" const="True" glidein_publish="True" job_publish="True" parameter="True" publish="True" type="string" value="%s"/>\n' % (n, v)
   return out[:-1]

def main():
    out_conf = ""

    cfg_all = merge_yaml()
    for site, cel in cfg_all.items():
        for gatekeeper, ceinfo in cel.items():
            conf_dict = get_dict(site, gatekeeper, ceinfo)
            conf_dict["attrs"] = get_attr_str(conf_dict["attrs"])
            out_conf += entry_stub % conf_dict
    print("<glidein>")
    print("    <entries>")
    print(out_conf[:-1])
    print("    </entries>")
    print("    <entry_sets>")
    print("    </entry_sets>")
    print("</glidein>")

if __name__ == "__main__":
    try:
        main()
    except MergeError as me:
        print(MergeError.codes_map[me.code])
        sys.exit(me.code)

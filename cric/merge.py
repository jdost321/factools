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
               <submit_attrs>%(submit_attrs)s
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

default_attr = {
    "const"           : "True",
    "glidein_publish" : "True",
    "job_publish"     : "False",
    "parameter"       : "True",
    "publish"         : "True",
    "type"            : "string"
}

class MergeError(Exception):
    """ Class to handle error in the merge script. Error codes:
    """
    codes_map = {
        1 : "1category.yml file not found",
        2 : "2category.yml file not found",
        3 : "3category.yml file not found",
        4 : "default.yml file not found",
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

def get_yaml_file_info(file_name, error_code):
    if not os.path.isfile(file_name):
        raise MergeError(error_code)
    with open(file_name) as fd:
        out = yaml.load(fd)

    return out

def merge_yaml():
    out = {}

    out = get_yaml_file_info("3category.yml", 3)
    gensites_info = get_yaml_file_info("2category.yml", 2)
    gencore_info = get_yaml_file_info("1category.yml", 1)
    defaults_info = get_yaml_file_info("default.yml", 4)

    for site, cel in out.items():
        for gatekeeper, ceinfo in cel.items():
            for entry, entryinfo in ceinfo.items():
                if entryinfo == None:
                    out[site][gatekeeper][entry] = gensites_info[site][gatekeeper][entry]
                    entryinfo = out[site][gatekeeper][entry]
                else:
                    update(entryinfo, gensites_info[site][gatekeeper][entry], overwrite=False)
                update(entryinfo, gencore_info[site][gatekeeper]["DEFAULT_ENTRY"])
                update(entryinfo, defaults_info["DEFAULT_SITE"]["DEFAULT_GETEKEEPER"]["DEFAULT_ENTRY"], overwrite=False)

    return out

def get_dict(gatekeeper, entry, entryinfo):
    out = {}
    out["gatekeeper"] = gatekeeper
    out["entry_name"] = entry
    out.update(entryinfo)
    return out

def get_attr_str(attrs):
    out = ""
    for name, d in sorted(attrs.items()):
        d["name"] = name
        update(d, default_attr, overwrite=False)
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
        out += '\n                  <submit_attr name="%s" value="%s"/>' % (n, v)
    return out

def main():
    out_conf = ""

    cfg_all = merge_yaml()
    for site, cel in cfg_all.items():
        for gatekeeper, ceinfo in cel.items():
            for entry, entryinfo in ceinfo.items():
                conf_dict = get_dict(gatekeeper, entry, entryinfo)
                conf_dict["attrs"] = get_attr_str(conf_dict["attrs"])
                if 'submit_attrs' in conf_dict:
                    conf_dict["submit_attrs"] = get_submit_attr_str(conf_dict["submit_attrs"])
                else:
                    conf_dict["submit_attrs"] = ""
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

from __future__ import division
from __future__ import print_function


import os
import sys
import yaml
import collections


# Template of entry configuration
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


# Default values of parameters attributes
default_attr = {
    "const": "True",
    "glidein_publish": "True",
    "job_publish": "False",
    "parameter": "True",
    "publish": "True",
    "type": "string"
}


# Class to handle error in the merge script
class MergeError(Exception):
    codes_map = {
        1: "1category.yml file not found",
        2: "2category.yml file not found",
        3: "3category.yml file not found",
        4: "default.yml file not found"
    }

    def __init__(self, code):
        self.code = code


# Update dictionary values
def update(data, update_data, overwrite=True):
    for key, value in update_data.items():
        if value == None:
            if key in data:
                del data[key]
        elif isinstance(value, collections.Mapping):
            data[key] = update(data.get(key, {}), value, overwrite)
        else:
            if overwrite or key not in data:
                data[key] = value

    return data


# Get data from yaml file
def get_yaml_file_info(file_name, error_code):
    if not os.path.isfile(file_name):
        raise MergeError(error_code)
    with open(file_name) as fd:
        out = yaml.load(fd)

    return out


# Merge data from all yaml files
def merge_yaml():
    out = {}
    out = get_yaml_file_info("3category.yml", 3)
    gensites_info = get_yaml_file_info("2category.yml", 2)
    gencore_info = get_yaml_file_info("1category.yml", 1)
    defaults_info = get_yaml_file_info("default.yml", 4)

    for site, ce_list in out.items():
        for gatekeeper, ce_info in ce_list.items():
            for entry, entry_info in ce_info.items():
                if entry_info == None:
                    out[site][gatekeeper][entry] = gensites_info[site][gatekeeper][entry]
                    entry_info = out[site][gatekeeper][entry]
                else:
                    update(entry_info, gensites_info[site][gatekeeper][entry], overwrite=False)
                update(entry_info, gencore_info[site][gatekeeper]["DEFAULT_ENTRY"])
                update(entry_info, defaults_info["DEFAULT_SITE"]["DEFAULT_GETEKEEPER"]["DEFAULT_ENTRY"], overwrite=False)

    return out


# Make dictionary to populate entry_stub variable
def get_dict(gatekeeper, entry, entry_info):
    out = {}
    out["gatekeeper"] = gatekeeper
    out["entry_name"] = entry
    out.update(entry_info)

    return out


# Collect all attributes
def get_attr_str(attrs):
    out = ""
    for name, data in sorted(attrs.items()):
        data["name"] = name
        update(data, default_attr, overwrite=False)
        if "comment" not in data:
            data["comment"] = ""
        else:
            data["comment"] = ' comment="' + data["comment"]  + '"'
        if "value" in data:
            out += '            <attr name="%(name)s"%(comment)s const="%(const)s" glidein_publish="%(glidein_publish)s" job_publish="%(job_publish)s" parameter="%(parameter)s" publish="%(publish)s" type="%(type)s" value="%(value)s"/>\n' % data

    return out[:-1]


# Collect all submit attributes
def get_submit_attr_str(submit_attrs):
    out = ""
    for name, value in sorted(submit_attrs.items()):
        out += '\n                  <submit_attr name="%s" value="%s"/>' % (name, value)

    return out


# Create entries configuration file
def write_to_file(file_name, data):
    with open(file_name, "w") as outfile:
        outfile.write("<glidein>\n")
        outfile.write("   <entries>\n")
        outfile.write(data)
        outfile.write("   </entries>\n")
        outfile.write("   <entry_sets>\n")
        outfile.write("   </entry_sets>\n")
        outfile.write("</glidein>\n")


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
                    conf_dict["gatekeeper"] = gatekeeper.split(":")[0] + " " + gatekeeper
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


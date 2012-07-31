#!/usr/bin/python

import sys
import os

STARTUP_DIR="/home/gfactory/glideinWMS/creation"
sys.path.append(os.path.join(STARTUP_DIR,"lib"))
sys.path.append(os.path.join(STARTUP_DIR,"../lib"))
import cgWParams
from ldapMonitor import LDAPQuery

# example additional_filter_str: (GlueCESEBindCEUniqueID=osg-gw-2.t2.ucsd.edu:2119/jobmanager-condor-default)
class BDIISEBindQuery(LDAPQuery):
    def __init__(self,
                 bdii_url,bdii_port=2170,     # where to find LDAP server
                 additional_filter_str=None,base_string="Mds-vo-name=local,o=grid"): # what to read
        if additional_filter_str==None:
            additional_filter_str=""
            
        #filter_str="&(GlueCEInfoContactString=*)%s"%additional_filter_str
        filter_str="&(GlueCESEBindSEUniqueID=*.*.*)%s"%additional_filter_str

        LDAPQuery.__init__(self,bdii_url,bdii_port,
                           base_string,filter_str)

    def fetch(self,additional_filter_str=None):
        out_data=LDAPQuery.fetch(self,additional_filter_str)
        for k in out_data.keys():
            cluster_id=k.split("Mds-Vo-name=",1)[1].split(",",1)[0]
            out_data[k]['Mds-Vo-name']=[cluster_id,'local']

        return out_data
        
    '''def filterStatus(self, usable=True):
        old_data=self.stored_data
        if old_data==None:
            raise RuntimeError, "No data loaded"
        new_data={}
        for k in old_data.keys():
            if (old_data[k]['GlueCEStateStatus'][0]=='Production')==usable:
                new_data[k]=old_data[k]
        self.stored_data=new_data
    '''

'''bdii_obj = BDIISEBindQuery(bdii_url="is.grid.iu.edu",additional_filter_str="(GlueCESEBindCEUniqueID=osg-gw-2.t2.ucsd.edu:2119/jobmanager-condor-default)")
bdii_data = bdii_obj.fetch()
print bdii_data[bdii_data.keys()[0]]['GlueCESEBindSEUniqueID']
'''

conf_file="glideinWMS.xml"
cparams=cgWParams.GlideinParams("dummy",os.path.join(STARTUP_DIR,"web_base"),["dummy",conf_file])

for entry in cparams.entries.keys():
    # for now skip ATLAS,CDF (assume they are non-us) and CMS sites already taken care of
    if (eval(cparams.entries[entry]['enabled']) and 'CMS' not in entry and 'ATLAS' not in entry and 'CDF' not in entry
        and not 'GLIDEIN_SEs' in cparams.entries[entry]['attrs'].keys() and len(cparams.entries[entry]['infosys_refs']) > 0):
        #print "%s %s" % (entry,cparams.entries[entry]['infosys_refs'][0]['ref'].split(',')[0].split('=')[1])
        bdii_obj = BDIISEBindQuery(bdii_url="is.grid.iu.edu",additional_filter_str="(GlueCESEBindCEUniqueID=%s)" % (cparams.entries[entry]['infosys_refs'][0]['ref'].split(',')[0].split('=')[1]))
        bdii_data = bdii_obj.fetch()
        bdii_data.keys()
        if len(bdii_data) == 0:
            print "%s SE not found! %s" % (entry,cparams.entries[entry]['infosys_refs'][0]['ref'])
        else:
            print "%s %s" % (entry,bdii_data[bdii_data.keys()[0]]['GlueCESEBindSEUniqueID'])

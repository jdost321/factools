#!/usr/bin/env python

from datetime import datetime
from dateutil.tz import tzutc
import urllib2

import xmltodict


def main():

    egi = get_egi()
    osg = get_osg()
    print "EGI:\n", egi 
    print "OSG:\n", osg

    all = egi.copy()
    all.update(osg)
    print "All:\n", all

def get_data (url):

    rq = urllib2.Request (url)
    xml_string = urllib2.urlopen(rq).read()
    data = xmltodict.parse (xml_string)

    return data

def get_egi():

    source_url = "https://goc.egi.eu/gocdbpi/public/?method=get_downtime&ongoing_only=yes"
    data = get_data(source_url)

    downtimes_in = data['results']['DOWNTIME']
    downtimes_out = {} 

    for record in downtimes_in:

        host = record['HOSTNAME']
        description = record['DESCRIPTION']
        start = datetime.fromtimestamp (int (record['START_DATE']), tzutc())
        end = datetime.fromtimestamp (int (record['END_DATE']), tzutc())

        # Repeated declaration of downtimes is always identical, and hence irrelevant                            
        """
        if host not in downtimes_out:
            new = {'start': start, 'end': end,
                    'description':description}
            downtimes_out[host] = new
        else:
            print "WARNING: host %s has more than one downtime record" % host

            if isinstance (downtimes_out[host], list):
                downtimes_out[host].append(new)
            else:
                multi = [ downtimes_out[host] ]
                multi.append(new)
                downtimes_out[host] = multi
        """
        downtimes_out[host] = {'start': start, 'end': end,
                               'description':description}

    return downtimes_out

def get_osg():

    source_url = "https://myosg.grid.iu.edu/rgdowntime/xml?summary_attrs_showservice=on&summary_attrs_showrsvstatus=on&summary_attrs_showfqdn=on&current_status_attrs_shownc=on&gip_status_attrs_showtestresults=on&downtime_attrs_showpast=&account_type=cumulative_hours&ce_account_type=gip_vo&se_account_type=vo_transfer_volume&bdiitree_type=total_jobs&bdii_object=service&bdii_server=is-osg&start_type=7daysago&end_type=now&all_resources=on&facility_10009=on&gridtype=on&gridtype_1=on&service_1=on&service_5=on&service_2=on&service_3=on&active=on&active_value=1&disable_value=1"

    data = get_data(source_url)
    downtimes_in = data['Downtimes']['CurrentDowntimes']['Downtime']
    downtimes_out = {}

    for record in downtimes_in:

        host = record['ResourceFQDN']
        description = record['Description']
        start = datetime.strptime (record['StartTime'].replace(" UTC",''), "%b %d, %Y %H:%M:%S").replace(tzinfo=tzutc())
        end = datetime.strptime (record['EndTime'].replace(" UTC",''), "%b %d, %Y %H:%M:%S").replace(tzinfo=tzutc())

        # Repeated declaration of downtimes is always identical, and hence irrelevant                            
        """
        if host not in downtimes_out:
            new = {'start': start, 'end': end,
                    'description':description}
            downtimes_out[host] = new
        else:
            print "WARNING: host %s has more than one downtime record" % host

            if isinstance (downtimes_out[host], list):
                downtimes_out[host].append(new)
            else:
                multi = [ downtimes_out[host] ]
                multi.append(new)
                downtimes_out[host] = multi
        """
        downtimes_out[host] = {'start': start, 'end': end,
                               'description':description}

    return downtimes_out


if __name__ == "__main__":
    main()

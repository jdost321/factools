#!/usr/bin/python

import xml.parsers.expat
import time
import sys

def start_element(name, attrs):
    global cur_site_name
    global is_CE
    global is_SE
    
    if name == 'site':
        cur_site_name = str(attrs['name'])
        sites[cur_site_name] = {}
        sites[cur_site_name]['CEs'] = []
        sites[cur_site_name]['SEs'] = []
        #print attrs['name']

    elif name == 'CE':
        is_CE = True

    elif name == 'SE':
        is_SE = True

def char_data(data):
    if is_CE or is_SE:
        data_buf.append(str(data))  

def end_element(name):
    global is_CE
    global is_SE
    global data_buf

    if name == 'CE':
        sites[cur_site_name]['CEs'].append("".join(data_buf))
        data_buf = []
        is_CE = False
    elif name == 'SE':
        sites[cur_site_name]['SEs'].append("".join(data_buf))
        data_buf = []
        is_SE = False

def log(out):
    print "%s %s" % (time.strftime('%F %T',time.localtime()),out)

xmlparser = xml.parsers.expat.ParserCreate()
xmlparser.StartElementHandler = start_element
xmlparser.CharacterDataHandler = char_data
xmlparser.EndElementHandler = end_element

# These need to be global for event handlers
sites = {}
is_CE = False
is_SE = False
cur_site_name = ''
# data buffer needed because CharacterDataHandler may be called more than once per element
data_buf = []

old_xml = sys.argv[1]
new_xml = sys.argv[2]

fin = open(old_xml)
xmlparser.ParseFile(fin)

fin.close()

old_db = sites

# re-initialize to parse new xml
xmlparser = xml.parsers.expat.ParserCreate()
xmlparser.StartElementHandler = start_element
xmlparser.CharacterDataHandler = char_data
xmlparser.EndElementHandler = end_element

sites = {}
is_CE = False
is_SE = False
cur_site_name = ''
data_buf = []

fin = open(new_xml)
xmlparser.ParseFile(fin)
fin.close()

new_db = sites

new_sites = set(new_db) - set(old_db)
for s in sorted(new_sites):
    print "New site: %s; CEs: %s, SEs: %s" % (s, new_db[s]['CEs'], new_db[s]['SEs'])

removed_sites = set(old_db) - set(new_db)
if removed_sites:
    print "Removed sites: %s" % (sorted(removed_sites))

same_sites = set(new_db) & set(old_db)

for site in sorted(same_sites):
    new_ces = set(new_db[site]['CEs']) - set(old_db[site]['CEs'])
    if new_ces:
        print "%s added CEs: %s" % (site, sorted(new_ces))
    old_ces = set(old_db[site]['CEs']) - set(new_db[site]['CEs'])
    if old_ces:
        print "%s removed CEs: %s" % (site, sorted(old_ces))
    new_ses = set(new_db[site]['SEs']) - set(old_db[site]['SEs'])
    if new_ses:
        print "%s added SEs: %s" % (site, sorted(new_ses))
    old_ses = set(old_db[site]['SEs']) - set(new_db[site]['SEs'])
    if old_ses:
        print "%s removed SEs: %s" % (site, sorted(old_ses))

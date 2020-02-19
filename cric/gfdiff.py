from __future__ import print_function

import re
import sys
import uuid
import base64
import hashlib
import argparse
import requests

from glideinwms.creation.lib.xmlConfig import DictElement, ListElement
from glideinwms.creation.lib.factoryXmlConfig import _parse, EntryElement, FactAttrElement, parse

last_key = [] 
tabs = 0
def count_tabs(function_to_decorate):
    def wrapper(*args, **kw):
        global tabs
        tabs += 1
        output = function_to_decorate(*args, **kw)
        tabs -= 1
    return wrapper


def check_list_diff(listA, listB):
    SKIP_TAGS = ['infosys_ref']
    for el in listA.children:
        if el.tag in SKIP_TAGS:
            continue
        if type(el)==DictElement:
            #print("\t"*tabs + "Checking %s" % el.tag)
            if len(listA.children) > 2:
                return
            #TODO what if B does not have it
            check_dict_diff(listA.children[0], listB.children[0],
                            lambda e: e.children.items())
        elif type(el)==FactAttrElement:
            #print("\t"*tabs + "Checking %s" % el['name'])
            elB = [ x for x in listB.children if x['name'] == el['name'] ]
            if len(elB) == 1:
                check_dict_diff(el, elB[0], FactAttrElement.items)
            elif len(elB) == 0:
                print("\t"*(tabs+1) + "%s: not present in %s" % (el['name'], entryB.getName()))
            else:
                print('More than one FactAttrElement')
        else:
            print('Element type not DictElement or FactAttrElement')
    for el in listB.children:
        if type(el)==FactAttrElement:
            elA = [ x for x in listA.children if x['name'] == el['name'] ]
            if len(elA) == 0:
                print("\t"*(tabs+1) + "%s: not present in %s" % (el['name'], entryA.getName()))


@count_tabs
def check_dict_diff(dictA, dictB, itemfunc=EntryElement.items, printName=True):
    global last_key
    tmpDictA = dict(itemfunc(dictA))
    tmpDictB = dict(itemfunc(dictB))
    SKIP_KEYS = ['name', 'comment']#, 'gatekeeper']
    for key, val in tmpDictA.items():
        last_key.append(key)
        #print("\t"*tabs + "Checking %s" % key)
        if key in SKIP_KEYS:
            continue
        if key not in tmpDictB:
            print("\t"*tabs + "Key %s(%s) not found in %s" % (key, val, entryB.getName()))
        elif type(val)==ListElement:
            check_list_diff(tmpDictA[key], tmpDictB[key])
        elif type(val)==DictElement:
            check_dict_diff(tmpDictA[key], tmpDictB[key], lambda e: e.children.items() if len(e.children)>0 else e.items())
        elif tmpDictA[key] != tmpDictB[key]:
            keystr = tmpDictA["name"] + ": " if printName and "name" in tmpDictA else last_key[-2] + ": "
            print("\t"*tabs + "%sKey %s is different: (%s vs %s)" %
                  (keystr, key, tmpDictA[key], tmpDictB[key]))
        last_key.pop()
    for key, val in tmpDictB.items():
        if key in SKIP_KEYS:
            continue
        if key not in tmpDictA:
            print("\t"*tabs + "Key %s(%s) not found in %s" % (key, val, entryA.getName()))


def parse_opts():
    """ Parse the command line options for this command
    """
    description = 'Do a diff of two entries\n\n'

    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument(
        '--confA', type=str, action='store', dest='confA',
        default='/etc/gwms-factory/glideinWMS.xml',
        help='Configuration for the first entry')

    parser.add_argument(
        '--confB', type=str, action='store', dest='confB',
        default='/etc/gwms-factory/glideinWMS.xml',
        help='Configuration for the first entry')

    parser.add_argument(
        '--entryA', type=str, action='store', dest='entryA',
        help='Configuration for the first entry')

    parser.add_argument(
        '--entryB', type=str, action='store', dest='entryB',
        help='Configuration for the first entry')

    parser.add_argument(
        '--mergely', action='count',
        help='Only print the mergely link')

    options = parser.parse_args()

    return options


def get_entry_text(entry, conf):
    with open(conf) as fd:
        text = fd.read()
        return re.search(".*( +<entry name=\"%s\".*?</entry>)" % entry, text, re.DOTALL).group(1)


def handle_mergely(entryA, confA, entryB, confB, mergely_only):
    url = 'http://www.mergely.com/ajax/handle_file.php'

    # get a unique 8char key
    unique_id = uuid.uuid4()
    myhash = hashlib.sha1(str(unique_id).encode("UTF-8"))     
    key = base64.b32encode(myhash.digest())[0:8]

    payload = {
        "key" : key,
        "name" : "lhs",
        "content" : get_entry_text(entryA, confA)
    }
    requests.post(url, data=payload)
    payload["name"] = "rhs"
    payload["content"] = get_entry_text(entryB, confB)
    requests.post(url, data=payload)
    requests.get("http://www.mergely.com/ajax/handle_save.php?key=" + key)
    if mergely_only:
        print("http://www.mergely.com/" + key)
    else:
        print("Visualize differences at: http://www.mergely.com/" + key)
        print()


def main():
    """ The main
    """
    global entryA
    global entryB
    options = parse_opts()

    if options.mergely:
        handle_mergely(options.entryA, options.confA, options.entryB, options.confB, options.mergely)
        return

    entryA = options.entryA
    entryB = options.entryB

    #conf = parse("/etc/gwms-factory/glideinWMS.xml")
    confA = _parse(options.confA)
    confB = _parse(options.confB)

    entryA = [ e for e in confA.get_entries() if e.getName()==entryA ]
    entryB = [ e for e in confB.get_entries() if e.getName()==entryB ]
    if len(entryA) != 1:
        print("Cannot find entry %s in the configuration file %s" % (options.entryA, options.confA))
        sys.exit(1)
    if len(entryB) != 1:
        print("Cannot find entry %s in the configuration file %s" % (options.entryB, options.confB))
        sys.exit(1)
    entryA = entryA[0]
    entryB = entryB[0]


    print("Checking entry attributes:")
    check_dict_diff(entryA, entryB, printName=False)
    print("Checking inner xml:")
    check_dict_diff(entryA.children, entryB.children, dict.items)


if __name__ == "__main__":
    main()

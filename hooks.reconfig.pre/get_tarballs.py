#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2009 Fermi Research Alliance, LLC
# SPDX-License-Identifier: Apache-2.0

# https://docs.google.com/spreadsheets/d/10WicpWi7O2K3m23WvIeZVE6rbX4PpHt8K9bXXOPHenM/edit#gid=0

import os
import re
import sys
import yaml
import argparse
import hashlib
import tempfile
import urllib.request
from urllib.parse import urljoin
from collections import UserDict
from html.parser import HTMLParser
from urllib.error import HTTPError
from distutils.version import StrictVersion


# Exit codes:
# 0: all good
# 1: file does not exist

class TarballManager(HTMLParser):
    def __init__(self, release_url, filenames, destination, verbose=False):
        HTMLParser.__init__(self)
        self.releases = []
        self.filenames = filenames
        self.release_url = release_url
        self.destination = destination
        self.downloaded_files = []
        self.latest_version = None # absolute latest, does not consider whitelists and blacklists
        self.verbose = verbose

        fp = urllib.request.urlopen(self.release_url)
        mybytes = fp.read()
        self.feed(mybytes.decode("utf-8"))
        if len(self.releases)==0:
            print(f"Cannot find any release in {self.release_url}")
        else: 
            self.releases.sort(key=StrictVersion)
            self.latest_version = self.releases[-1]

    def handle_data(self, data):
        if re.match(r"\d+\.\d+\.\d+/" , data):
            try:
                urllib.request.urlopen(self.release_url + "/" + data + "release")
            except HTTPError as err:
                if err.getcode() != 404:
                    raise
            else:
                self.releases.append(data[:-1])

    def download_tarballs(self, version):
        desturl = os.path.join(self.release_url, version, "release/") # urljoin needs nested call and manual adding of "/".. It sucks. 
        checksums = {}
        with tempfile.TemporaryDirectory() as tmp_dir:
            hash_file = os.path.join(tmp_dir, "sha256sum.txt")
            urllib.request.urlretrieve(urljoin(desturl, "sha256sum.txt"), hash_file)
            
            with open(hash_file, 'r') as hf:
                for line in hf:
                    fhash, filename = line.split('  ')
                    checksums[filename.strip()] = fhash.strip()

        for fname in self.filenames:
            tname = fname.format(version=version) # tarball name
            dest_file = os.path.join(self.destination, tname)
            if os.path.isfile(dest_file):
                if self.verify_checksum(tname, checksums):
                    self.verbose and print(f"\tFile {dest_file} already exists. Continuing with next file")
                    self.downloaded_files.append(dest_file)
                    continue
                else:
                    print(f"\tRe-downloading {dest_file} since it exists but it has a wrong checksum (or checkusm does not exist)")

            try:
                urllib.request.urlretrieve(urljoin(desturl, tname), dest_file)
            except urllib.error.HTTPError as err:
                if err.getcode() == 404:
                    self.verbose and print(f"\tFile {tname} is not available at {desturl}. Continuing with next file")
                    continue
                else:
                    raise
            isok = self.verify_checksum(tname, checksums)
            if isok == True:
                print(f"\tFile {tname} successfully downloaded")
                self.downloaded_files.append(dest_file)
            elif isok == False:
                print(f"\tChecksum verification failed for file {tname} at {desturl}. Continuing with next file")
            elif isok == None:
                print(f"\tFile {tname} successfully downloaded but checksum not available at {desturl} (check 'sha256sum.txt')")

    def verify_checksum(self, tname, checksums):
        dest_file = os.path.join(self.destination, tname)
        with open(dest_file, 'rb') as f:
            tar_content = f.read()
            actual_checksum = hashlib.sha256(tar_content).hexdigest()

        try:
            return actual_checksum==checksums[tname]
        except KeyError:
            return None

    def generate_xml(self, os_map, arch_map, whitelist, blacklist, default_tarball_version):
        xml_snippet = '      <condor_tarball arch="{arch}" os="{os}" tar_file="{dest_file}" version="{version}"/>\n'

        if whitelist != []:
            latest_version = sorted(whitelist, key=StrictVersion)[-1]
        else:
            versions = list(set(self.releases) - set(blacklist))
            latest_version = sorted(versions, key=StrictVersion)[-1]
            
        out = ""
        for dest_file in self.downloaded_files:
            _, sversion, os_arch, _ = os.path.basename(dest_file).split("-")
            arch, opsystem = os_arch.rsplit("_", 1)
            version = sversion # sversion = "split" version
            if sversion == latest_version:
                major, minor, _ = sversion.split('.')
                version += ','+major+'.0.x' if minor=='0' else ','+major+'.x'
            if sversion in default_tarball_version:
                version += ",default" 
            out += xml_snippet.format(arch=arch_map[arch], os=os_map[opsystem], dest_file=dest_file, version=version)
        return out


class Config(UserDict):
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_file = os.environ.get("GET_TARBALLS_CONFIG", False) or os.path.join(script_dir, "get_tarballs.yaml")
        if not os.path.isfile(config_file):
            print(f"Configuration file {config_file} does not exist")
            sys.exit(1)
        with open(config_file) as cf:
            config = yaml.load(cf, Loader=yaml.FullLoader)
        self.data = config
        self.validate()

    def validate(self):
        for major_dict in self["CONDOR_TARBALL_LIST"]:
            if "WHITELIST" not in major_dict:
                major_dict["WHITELIST"] = []
            if "BLACKLIST" not in major_dict:
                major_dict["BLACKLIST"] = []
            if "latest" in major_dict["WHITELIST"]:
                major_dict["WHITELIST"].remove("latest")
                major_dict["DOWNLOAD_LATEST"] = True
            major_dict["WHITELIST"].sort(key=StrictVersion)
            major_dict["BLACKLIST"].sort(key=StrictVersion)


def check_xml(release):
    found = False
    with open("/etc/gwms-factory/glideinWMS.xml","r") as myfile:
        for line in myfile:
            if re.search(f"condor_tarball.*{release}", line):
                found = True
    return found


def save_xml(dest_xml, xml):
    with open(dest_xml, "w") as fd:
        fd.write("<glidein>\n")
        fd.write("   <condor_tarballs>\n")
        fd.write(xml)
        fd.write("   </condor_tarballs>\n")
        fd.write("</glidein>\n")


def parse_opts():
    parser = argparse.ArgumentParser(prog="get_tarballs")

    parser.add_argument(
        "--verbose",
        action='store_true',
        help="Be more loud when downloading tarballs file"
    )

    args = parser.parse_args()

    return args


def main():
    args = parse_opts()
    config = Config()
    release_url = config["TARBALL_BASE_URL"]
    default_tarball_version = config["DEFAULT_TARBALL_VERSION"]
    xml = ""
    
    for major_dict in config["CONDOR_TARBALL_LIST"]:
        print(f'Handling major version {major_dict["MAJOR_VERSION"]}')
        major_version = major_dict["MAJOR_VERSION"]
        manager = TarballManager(urljoin(release_url, major_version), config["FILENAME_LIST"], config["DESTINATION_DIR"], args.verbose)
        # If necessary, add the latest version to the whitelist now that we know the latest version for this major set of releases
        if major_dict.get("DOWNLOAD_LATEST", False):
            major_dict["WHITELIST"].append(manager.latest_version)
        # I think CHACK_LATEST can be deprecated now that we have DOWNLOAD_LATEST
        if major_dict.get("CHECK_LATEST", False) == True and not check_xml(manager.latest_version):
            print(f"Latest version {manager.latest_version} not present in the glideinWMS.xml file.")
        if major_dict["WHITELIST"] != []:
            # Just get whitelisted versions
            for version in major_dict["WHITELIST"]:
                manager.download_tarballs(version)
        else:
            # Get everything but the blacklisted
            to_download = sorted(set(manager.releases) - set(major_dict["BLACKLIST"]), key=StrictVersion)
            for version in to_download:
                manager.download_tarballs(version)
        xml += manager.generate_xml(config["OS_MAP"], config["ARCH_MAP"], major_dict["WHITELIST"], major_dict["BLACKLIST"],
                                    manager.latest_version if default_tarball_version == "latest" else default_tarball_version)

    if config.get("XML_OUT") is not None:
        try:
            save_xml(config["XML_OUT"], xml)
        except IOError as ioex:
            print(f'Cannot write file {config["XML_OUT"]} when trying to save xml tarball output: {str(ioex)}')


if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2023-2024 Hirochika Asai <asai@jar.jp>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import cisco_gnmi
import json
import os
import errno
import argparse
import time

## Arguments
parser = argparse.ArgumentParser()
parser.add_argument('--host', type=str, default='localhost')
parser.add_argument('--port', type=int, default=9339)
parser.add_argument('--cacert', type=str, default='rootCA.pem')
parser.add_argument('--private-key', type=str, default='client.key')
parser.add_argument('--cert-chain', type=str, default='client.crt')

## Parse the arguments
args = parser.parse_args()

## Target controller
target = '%s:%d' % (args.host, args.port)

## Interval (in seconds)
interval = 60

## Data directory
databasedir = './data'

## Initialize the GNMI client
client = cisco_gnmi.ClientBuilder(target).set_os('IOS XE').set_secure_from_file(
    root_certificates=args.cacert,
    private_key=args.private_key,
    certificate_chain=args.cert_chain,
).construct()


"""
Create a symbolic link (overwrite if exists)
"""
def symlink_overwrite(f1, f2):
    try:
        os.symlink(f1, f2)
    except OSError as e:
        if e.errno == errno.EEXIST:
            os.remove(f2)
            os.symlink(f1, f2)
        else:
            raise e

"""
Main routine
"""
def main():
    xpaths = ['Cisco-IOS-XE-wireless-rrm-oper:rrm-oper-data/rrm-measurement',
              'Cisco-IOS-XE-wireless-access-point-oper:access-point-oper-data/ap-name-mac-map',
              'Cisco-IOS-XE-wireless-access-point-oper:access-point-oper-data/capwap-data',
              'Cisco-IOS-XE-wireless-access-point-oper:access-point-oper-data/radio-oper-data',
              'Cisco-IOS-XE-wireless-access-point-oper:access-point-oper-data/radio-oper-stats']


    while True:
        obj_rrm = {}
        obj_ap = {}
        ts = None
        response = client.get_xpaths(xpaths, encoding="JSON_IETF", data_type='STATE')
        for msg in response.notification:
            ts = msg.timestamp
            for um in msg.update:
                ## RRM
                if um.path.elem[0].name == 'Cisco-IOS-XE-wireless-rrm-oper:rrm-oper-data':
                    if um.path.elem[1].name == 'rrm-measurement':
                        jm = dict(um.path.elem[1].key)
                        jm.update(json.loads(um.val.json_ietf_val))
                        if 'rrm-measurement' not in obj_rrm:
                            obj_rrm['rrm-measurement'] = []
                        obj_rrm['rrm-measurement'].append(jm)
                ## AP
                elif um.path.elem[0].name == 'Cisco-IOS-XE-wireless-access-point-oper:access-point-oper-data':
                    if um.path.elem[1].name == 'ap-name-mac-map':
                        jm = dict(um.path.elem[1].key)
                        jm.update(json.loads(um.val.json_ietf_val))
                        if 'ap-name-mac-map' not in obj_ap:
                            obj_ap['ap-name-mac-map'] = []
                        obj_ap['ap-name-mac-map'].append(jm)
                    elif um.path.elem[1].name == 'capwap-data':
                        jm = dict(um.path.elem[1].key)
                        jm.update(json.loads(um.val.json_ietf_val))
                        if 'capwap-data' not in obj_ap:
                            obj_ap['capwap-data'] = []
                        obj_ap['capwap-data'].append(jm)
                    elif um.path.elem[1].name == 'radio-oper-data':
                        jm = dict(um.path.elem[1].key)
                        jm.update(json.loads(um.val.json_ietf_val))
                        if 'radio-oper-data' not in obj_ap:
                            obj_ap['radio-oper-data'] = []
                        obj_ap['radio-oper-data'].append(jm)
                    elif um.path.elem[1].name == 'radio-oper-stats':
                        jm = dict(um.path.elem[1].key)
                        jm.update(json.loads(um.val.json_ietf_val))
                        if 'radio-oper-stats' not in obj_ap:
                            obj_ap['radio-oper-stats'] = []
                        obj_ap['radio-oper-stats'].append(jm)
        if ts is not None:
            fname = '%d.json' % ts
            ## RRM
            obj_rrm['timestamp'] = ts
            js = json.dumps(obj_rrm, indent=2)
            file_path = '%s/rrm/%s' % (databasedir, fname)
            rrm_path = '%s/rrm.json' % databasedir
            rrm_prev_path = '%s/rrm.prev.json' % databasedir
            with open(file_path, mode='w') as f:
                f.write(js)
            ## Get old reference
            oldref = None
            if os.path.islink(rrm_prev_path):
                oldref = os.path.realpath(rrm_prev_path)
            try:
                os.rename(rrm_path, rrm_prev_path)
            except OSError as e:
                if e.errno == errno.ENOENT:
                    pass
                else:
                    raise
            ## Create a symbolic link
            symlink_overwrite(os.path.relpath(file_path, databasedir), rrm_path)
            if oldref:
                os.remove(oldref)
            ## AP
            obj_ap['timestamp'] = ts
            js = json.dumps(obj_ap, indent=2)
            file_path = '%s/ap/%s' % (databasedir, fname)
            ap_path = '%s/ap.json' % databasedir
            ap_prev_path = '%s/ap.prev.json' % databasedir
            with open(file_path, mode='w') as f:
                f.write(js)
            ## Get old reference
            oldref = None
            if os.path.islink(ap_prev_path):
                oldref = os.path.realpath(ap_prev_path)
            try:
                os.rename(ap_path, ap_prev_path)
            except OSError as e:
                if e.errno == errno.ENOENT:
                    pass
                else:
                    raise
            ## Create a symbolic link
            symlink_overwrite(os.path.relpath(file_path, databasedir), ap_path)
            if oldref:
                os.remove(oldref)
        time.sleep(interval)

if __name__ == "__main__":
    main()

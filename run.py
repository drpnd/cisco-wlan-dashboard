#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2023 Hirochika Asai <asai@jar.jp>

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
    xpaths = ['Cisco-IOS-XE-wireless-rrm-oper:rrm-oper-data', 'Cisco-IOS-XE-wireless-access-point-oper:access-point-oper-data/radio-oper-data']

    for msg in client.subscribe_xpaths(xpaths, encoding="JSON_IETF", sample_interval=(10**9) * interval, sub_mode='SAMPLE'):
        if msg.sync_response:
            pass
        else:
            ts = msg.update.timestamp
            fname = '%d.json' % ts
            for um in msg.update.update:
                ## RRM
                if um.path.elem[0].name == 'Cisco-IOS-XE-wireless-rrm-oper:rrm-oper-data':
                    jm = json.loads(um.val.json_ietf_val)
                    js = json.dumps(jm, indent=2)
                    file_path = '%s/rrm/%s' % (databasedir, fname)
                    rrm_path = '%s/rrm.json' % databasedir
                    rrm_prev_path = '%s/rrm.prev.json' % databasedir
                    with open(file_path, mode='w') as f:
                        f.write(js)
                    try:
                        os.rename(rrm_path, rrm_prev_path)
                    except OSError as e:
                        if e.errno == errno.ENOENT:
                            pass
                        else:
                            raise
                    symlink_overwrite(os.path.relpath(file_path, databasedir), rrm_path)
                ## AP
                elif um.path.elem[0].name == 'Cisco-IOS-XE-wireless-access-point-oper:access-point-oper-data':
                    jm = json.loads(um.val.json_ietf_val)
                    js = json.dumps(jm, indent=2)
                    file_path = '%s/ap/%s' % (databasedir, fname)
                    ap_path = '%s/ap.json' % databasedir
                    ap_prev_path = '%s/ap.prev.json' % databasedir
                    with open(file_path, mode='w') as f:
                        f.write(js)
                    try:
                        os.rename(ap_path, ap_prev_path)
                    except OSError as e:
                        if e.errno == errno.ENOENT:
                            pass
                        else:
                            raise
                    symlink_overwrite(os.path.relpath(file_path, databasedir), ap_path)

if __name__ == "__main__":
    main()


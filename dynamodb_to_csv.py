#!/usr/bin/env python3
"""
dynamodb_to_csv.py
==================

Python3 / boto3 script to dump all data in a DynamoDB table to CSV.

Requirements
------------

* Python 3.4+
* boto3

Canonical Source
----------------

https://github.com/jantman/misc-scripts/blob/master/dynamodb_to_csv.py

License
-------

Copyright 2019 Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
Free for any use provided that patches are submitted back to me.

CHANGELOG
---------

2019-02-20 Jason Antman <jason@jasonantman.com>:
  - initial version of script
"""

import sys
import argparse
import logging
import csv
import io
import json

try:
    import boto3
except ImportError:
    sys.stderr.write("ERROR: You must 'pip install boto3'")
    raise SystemExit(1)


FORMAT = '%(asctime)s %(levelname)s:%(name)s:%(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger()

for lname in ['urllib3', 'boto3', 'botocore']:
    l = logging.getLogger(lname)
    l.setLevel(logging.WARNING)
    l.propagate = True


class DynamoDumper(object):

    def __init__(self):
        logger.debug('Connecting to DynamoDB')
        self._dynamo = boto3.resource('dynamodb')

    def run(self, table_name, fields=None, sort_field=None):
        records, all_fields = self._get_data(table_name)
        if fields is None:
            fields = sorted(all_fields)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fields, restval='')
        writer.writeheader()
        rownum = 0
        if sort_field is not None:
            records = sorted(records, key=lambda x: x[sort_field])
        for r in records:
            rownum += 1
            for k, v in r.items():
                # format lists nicely
                if isinstance(v, type([])):
                    r[k] = ', '.join(v)
            writer.writerow(r)
        print(output.getvalue())

    def _get_data(self, table_name):
        table = self._dynamo.Table(table_name)
        all_fields = set()
        records = []
        logger.info('Scanning DynamoDB table: %s', table_name)
        for item in table.scan()['Items']:
            records.append(item)
            for k in item.keys():
                all_fields.add(k)
        logger.debug('Retrieved %d records from DynamoDB', len(records))
        return records, list(all_fields)


def parse_args(argv):
    p = argparse.ArgumentParser(description='Dump DynamoDB table to CSV')
    p.add_argument('-f', '--field-order', dest='field_order', action='store',
                   type=str, default=None,
                   help='CSV list of field names, to output columns in this '
                        'order. Fields not listed will not be output. If not '
                        'specified, will output all fields in alphabetical '
                        'order.')
    p.add_argument('-s', '--sort-field', dest='sort_field', type=str,
                   action='store', default=None,
                   help='Optional, name of field to sort on')
    p.add_argument('TABLE_NAME', action='store', type=str,
                   help='DynamoDB table name to dump')
    args = p.parse_args(argv)
    return args


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    if args.field_order is not None:
        args.field_order = args.field_order.split(',')
    DynamoDumper().run(
        args.TABLE_NAME, fields=args.field_order, sort_field=args.sort_field
    )

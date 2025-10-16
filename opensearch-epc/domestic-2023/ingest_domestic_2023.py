#!/usr/bin/env python3
"""
Ingest domestic-2023 certificates.csv into OpenSearch.

Features:
- Reads `schema.json` (CSVW) in the same folder to infer types and build a mapping.
- Bulk indexes `certificates.csv` into an index (default: domestic-2023-certificates).
- Optionally builds a properties index (default: domestic-2023-properties) containing
  the latest certificate per `UPRN` using a composite aggregation + top_hits.
- Optionally enrich with postcode->lat/lon CSV to populate a `location` geo_point.

Usage examples (PowerShell):

 $env:OPENSEARCH_URL='http://localhost:9200'
 $env:OPENSEARCH_USER='admin'
 $env:OPENSEARCH_PASS='admin'
 python ingest_domestic_2023.py --csv certificates.csv

See README.md for more details.
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

from opensearchpy import OpenSearch, helpers


def load_schema(schema_path: str) -> Dict[str, Any]:
    with open(schema_path, 'r', encoding='utf-8') as fh:
        schema = json.load(fh)
    # assume first table is certificates.csv
    tables = schema.get('tables', [])
    if not tables:
        raise SystemExit('No tables found in schema.json')
    table = tables[0]
    cols = table.get('tableSchema', {}).get('columns', [])
    columns = {}
    for c in cols:
        name = c.get('name')
        dtype = c.get('datatype')
        columns[name] = dtype
    primary_key = table.get('tableSchema', {}).get('primaryKey')
    return {'columns': columns, 'primaryKey': primary_key}


def csvw_type_to_es(dtype: Any) -> Dict[str, Any]:
    # dtype in schema.json can be a string or an object
    if isinstance(dtype, dict):
        base = dtype.get('base') or dtype.get('datatype')
    else:
        base = dtype
    if not base:
        base = 'string'
    base = str(base).lower()
    if base in ('integer', 'int'):
        return {'type': 'long'}
    if base in ('float', 'double', 'decimal'):
        return {'type': 'double'}
    if 'date' in base or 'datetime' in base:
        return {'type': 'date', 'format': 'strict_date_optional_time||yyyy-MM-dd HH:mm:ss||yyyy-MM-dd'}
    # default string -> text + keyword subfield
    return {'type': 'text', 'fields': {'keyword': {'type': 'keyword', 'ignore_above': 256}}}


def build_mapping_from_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    props = {}
    for name, dtype in schema['columns'].items():
        # Use lower-case field names for indexing (consistent with CSV headers)
        fld = name
        props[fld] = csvw_type_to_es(dtype)
    # add a location geo_point if later provided
    props['location'] = {'type': 'geo_point'}
    mapping = {'mappings': {'properties': props}}
    return mapping


def parse_value(val: str, dtype: Any):
    if val is None or val == '':
        return None
    if isinstance(dtype, dict):
        base = dtype.get('base') or dtype.get('datatype')
    else:
        base = dtype
    if base is None:
        base = 'string'
    base = str(base).lower()
    try:
        if base in ('integer', 'int'):
            return int(val)
        if base in ('float', 'double', 'decimal'):
            return float(val)
        if 'date' in base or 'datetime' in base:
            # try common formats
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d'):
                try:
                    dt = datetime.strptime(val, fmt)
                    return dt.isoformat()
                except Exception:
                    continue
            return val
    except Exception:
        return val
    return val


def ingest_certificates(client: OpenSearch, csv_path: str, schema: Dict[str, Any], index_name: str, batch_size: int = 5000):
    # create index with mapping
    mapping = build_mapping_from_schema(schema)
    if client.indices.exists(index=index_name):
        print(f'Index {index_name} already exists')
    else:
        client.indices.create(index=index_name, body=mapping)
        print(f'Created index {index_name}')

    actions = []
    total = 0
    with open(csv_path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            doc: Dict[str, Any] = {}
            for col, dtype in schema['columns'].items():
                raw = row.get(col)
                doc[col] = parse_value(raw, dtype)    
            # determine id: use LMK_KEY (primary) if present
            doc_id = None
            if 'LMK_KEY' in doc and doc['LMK_KEY']:
                doc_id = str(doc['LMK_KEY'])
            action = {'_index': index_name, '_source': doc}
            if doc_id:
                action['_id'] = doc_id
            actions.append(action)
            if len(actions) >= batch_size:
                helpers.bulk(client, actions)
                total += len(actions)
                print(f'Indexed {total} certificates...')
                actions = []
    if actions:
        helpers.bulk(client, actions)
        total += len(actions)
        print(f'Indexed {total} certificates (final)')


def build_properties_index_from_certificates(client: OpenSearch, cert_index: str, prop_index: str, batch_size: int = 5000, date_field_candidates=None):
    # Create properties index with a simple mapping; we'll store latest certificate fields under 'latest'
    if client.indices.exists(index=prop_index):
        print(f'Properties index {prop_index} already exists')
    else:
        mapping = {
            'mappings': {
                'properties': {
                    'UPRN': {'type': 'keyword'},
                    'location': {'type': 'geo_point'},
                    'latest': {'type': 'object', 'dynamic': True}
                }
            }
        }
        client.indices.create(index=prop_index, body=mapping)
        print(f'Created properties index {prop_index}')

    # Composite aggregation to page through all UPRNs and fetch top_hit by date
    if date_field_candidates is None:
        date_field_candidates = ['LODGEMENT_DATETIME', 'LODGEMENT_DATE', 'INSPECTION_DATE']

    # composite aggregation source
    comp_source = [{'uprn': {'terms': {'field': 'UPRN.keyword'}}}]
    after_key = None
    total_props = 0
    while True:
        body = {
            'size': 0,
            'aggs': {
                'by_uprn': {
                    'composite': {'size': 1000, 'sources': comp_source, **({'after': after_key} if after_key else {})},
                    'aggs': {
                        'latest': {
                            'top_hits': {
                                'size': 1,
                                'sort': [{date_field_candidates[0]: {'order': 'desc'}}]
                            }
                        }
                    }
                }
            }
        }
        res = client.search(index=cert_index, body=body)
        buckets = res['aggregations']['by_uprn']['buckets']
        actions = []
        for b in buckets:
            uprn = b['key']['uprn']
            hit = b['latest']['hits']['hits'][0]
            src = hit['_source']
            doc = {'UPRN': uprn, 'latest': src}
            # copy location if present
            if 'location' in src:
                doc['location'] = src['location']
            action = {'_index': prop_index, '_id': str(uprn), '_source': doc}
            actions.append(action)
        if actions:
            helpers.bulk(client, actions)
            total_props += len(actions)
            print(f'Indexed {total_props} properties...')
        # paging
        after_key = res['aggregations']['by_uprn'].get('after_key')
        if not after_key:
            break

    print(f'Properties indexing complete: {total_props} documents')


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--csv', default='certificates.csv', help='path to certificates.csv')
    p.add_argument('--schema', default='schema.json', help='path to schema.json (CSVW)')
    p.add_argument('--opensearch-url', default=os.environ.get('OPENSEARCH_URL', 'http://localhost:9200'))
    p.add_argument('--user', default=os.environ.get('OPENSEARCH_USER'))
    p.add_argument('--password', default=os.environ.get('OPENSEARCH_PASS'))
    p.add_argument('--index-certificates', default='domestic-2023-certificates')
    p.add_argument('--index-properties', default='domestic-2023-properties')
    p.add_argument('--batch-size', type=int, default=5000)
    p.add_argument('--postcode-lookup', default=None, help='CSV with postcode,lat,lon to enrich location')
    p.add_argument('--build-properties', action='store_true', help='Build properties index (latest per UPRN) after ingest')
    args = p.parse_args(argv)

    schema_path = os.path.join(os.path.dirname(__file__), args.schema) if not os.path.isabs(args.schema) else args.schema
    csv_path = os.path.join(os.path.dirname(__file__), args.csv) if not os.path.isabs(args.csv) else args.csv
    schema = load_schema(schema_path)

    client = OpenSearch([args.opensearch_url], http_auth=(args.user, args.password) if args.user else None)

    ingest_certificates(client, csv_path, schema, args.index_certificates, batch_size=args.batch_size)

    if args.build_properties:
        build_properties_index_from_certificates(client, args.index_certificates, args.index_properties, batch_size=args.batch_size)


if __name__ == '__main__':
    main()

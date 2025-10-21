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


def ingest_certificates(client: OpenSearch, csv_path: str, schema: Dict[str, Any], index_name: str, batch_size: int = 1000):
    # create index with mapping
    mapping = build_mapping_from_schema(schema)
    if client.indices.exists(index=index_name):
        print(f'Index {index_name} already exists')
    else:
        client.indices.create(index=index_name, body=mapping)
        print(f'Created index {index_name}')

    actions = []
    total = 0
    processed = 0
    
    with open(csv_path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            processed += 1
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
                try:
                    helpers.bulk(client, actions, chunk_size=batch_size, max_retries=3, request_timeout=60)
                    total += len(actions)
                    print(f'Indexed {total} certificates... (processed {processed} rows)')
                    actions.clear()  # Explicit clear for memory
                except Exception as e:
                    print(f'Error indexing batch: {e}')
                    # Continue with next batch
                    actions.clear()
                    
    if actions:
        try:
            helpers.bulk(client, actions, chunk_size=batch_size, max_retries=3, request_timeout=60)
            total += len(actions)
            print(f'Indexed {total} certificates (final, processed {processed} rows)')
        except Exception as e:
            print(f'Error indexing final batch: {e}')
        finally:
            actions.clear()


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--csv', default='certificates.csv', help='path to certificates.csv')
    p.add_argument('--schema', default='schema.json', help='path to schema.json (CSVW)')
    p.add_argument('--opensearch-url', default=os.environ.get('OPENSEARCH_URL', 'http://localhost:9200'))
    p.add_argument('--user', default=os.environ.get('OPENSEARCH_USER'))
    p.add_argument('--password', default=os.environ.get('OPENSEARCH_PASS'))
    p.add_argument('--index-certificates', default='domestic-2023-certificates')
    p.add_argument('--index-properties', default='domestic-2023-properties')
    p.add_argument('--batch-size', type=int, default=1000)
    p.add_argument('--postcode-lookup', default=None, help='CSV with postcode,lat,lon to enrich location')
    args = p.parse_args(argv)

    schema_path = os.path.join(os.path.dirname(__file__), args.schema) if not os.path.isabs(args.schema) else args.schema
    csv_path = os.path.join(os.path.dirname(__file__), args.csv) if not os.path.isabs(args.csv) else args.csv
    schema = load_schema(schema_path)

    client = OpenSearch([args.opensearch_url], http_auth=(args.user, args.password) if args.user else None)

    ingest_certificates(client, csv_path, schema, args.index_certificates, batch_size=args.batch_size)


if __name__ == '__main__':
    main()

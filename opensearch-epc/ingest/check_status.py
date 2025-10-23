#!/usr/bin/env python3
"""
Status checking script for domestic EPC certificates.
This script checks the current status of certificate ingestion.
"""

import argparse
import os
from opensearchpy import OpenSearch

def get_document_count(client: OpenSearch, index_name: str) -> int:
    """Get the current document count in an index."""
    try:
        result = client.count(index=index_name)
        return result['count']
    except Exception as e:
        print(f"Error getting count for {index_name}: {e}")
        return 0

def main():
    p = argparse.ArgumentParser(description="Check EPC ingestion status")
    p.add_argument('--opensearch-url', default=os.environ.get('OPENSEARCH_URL', 'http://localhost:9200'))
    p.add_argument('--user', default=os.environ.get('OPENSEARCH_USER', 'admin'))
    p.add_argument('--password', default=os.environ.get('OPENSEARCH_PASS', 'admin'))
    p.add_argument('--index-certificates', default='domestic-2023-certificates')
    
    args = p.parse_args()
    
    # OpenSearch client
    client = OpenSearch(
        hosts=[args.opensearch_url],
        http_auth=(args.user, args.password) if args.user and args.password else None,
        use_ssl=False,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False
    )
    
    # Check current status
    cert_count = get_document_count(client, args.index_certificates)
    print(f"Certificates index ({args.index_certificates}): {cert_count:,} documents")

if __name__ == '__main__':
    main()
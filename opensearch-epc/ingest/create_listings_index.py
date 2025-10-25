#!/usr/bin/env python3
"""
Create the listings index and aliases in OpenSearch.

Usage:
  python create_listings_index.py \
    --opensearch-url http://localhost:9200 --user admin --password admin \
    --index listings-v1 --active-alias listings-active --all-alias listings-all

Environment variables (optional):
  OPENSEARCH_URL, OPENSEARCH_USER, OPENSEARCH_PASS
"""

import argparse
import json
import os
from opensearchpy import OpenSearch


def load_mapping(mapping_path: str) -> dict:
    with open(mapping_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Create listings index and aliases")
    parser.add_argument("--opensearch-url", default=os.environ.get("OPENSEARCH_URL", "http://localhost:9200"))
    parser.add_argument("--user", default=os.environ.get("OPENSEARCH_USER"))
    parser.add_argument("--password", default=os.environ.get("OPENSEARCH_PASS"))
    parser.add_argument("--index", default="listings-v1")
    parser.add_argument("--active-alias", default="listings-active")
    parser.add_argument("--all-alias", default="listings-all")
    parser.add_argument("--mapping", default=os.path.join(os.path.dirname(__file__), "listings-v1.mapping.json"))
    parser.add_argument("--force", action="store_true", help="Delete existing index if it exists")
    args = parser.parse_args()

    client = OpenSearch(
        [args.opensearch_url],
        http_auth=(args.user, args.password) if args.user else None,
        use_ssl=args.opensearch_url.startswith("https"),
        verify_certs=False,
        ssl_show_warn=False,
    )

    if client.indices.exists(index=args.index):
        if not args.force:
            print(f"Index {args.index} already exists. Use --force to re-create.")
            return 0
        print(f"Deleting existing index {args.index}...")
        client.indices.delete(index=args.index)

    mapping = load_mapping(args.mapping)
    print(f"Creating index {args.index}...")
    client.indices.create(index=args.index, body=mapping)

    # Setup aliases
    actions = [
        {"add": {"index": args.index, "alias": args.all_alias}},
        {
            "add": {
                "index": args.index,
                "alias": args.active_alias,
                "filter": {"term": {"is_active": True}},
            }
        },
    ]
    client.indices.update_aliases(body={"actions": actions})
    print(f"Created aliases: {args.all_alias}, {args.active_alias}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

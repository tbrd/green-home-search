#!/usr/bin/env python3
"""
Minimal listings ingest/enrichment script (skeleton).

Reads listing payloads (e.g., from a CSV/JSON feed), enriches with property fields
from the properties index (by property_id=UPRN), and upserts into the listings index.

This is a skeleton demonstrating the data flow. Adapt the `iter_listings()` function
to your feed, and map fields as needed.

Usage (example):
  python ingest_listings.py \
    --opensearch-url http://localhost:9200 --user admin --password admin \
    --properties-index properties --listings-index listings-v1

Environment variables (optional): OPENSEARCH_URL, OPENSEARCH_USER, OPENSEARCH_PASS
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone
from typing import Dict, Any, Iterable, Optional, List

from opensearchpy import OpenSearch, helpers


def iter_listings() -> Iterable[Dict[str, Any]]:
    """Yield raw listing docs from your source system.

    Replace with your real feed reader. For now we yield a tiny example.
    Required fields to resolve/enrich:
      - property_id (UPRN)
      - listing_id (deterministic; e.g., {source}:{external_id})
      - bedrooms, price, address_line, postcode, location (lat/lon) if available
      - status/is_active, listed_at, expires_at
    """
    now = datetime.now(timezone.utc).isoformat()
    yield {
        "listing_id": "example:abc123",
        "property_id": "UPRN-EXAMPLE-1",
        "source": "example",
        "external_id": "abc123",
        "status": "active",
        "is_active": True,
        "listed_at": now,
        "price": 350000,
        "currency": "GBP",
        "bedrooms": 3,
        "address_line": "1 High Street, Amersham",
        "postcode": "HP7 0XX",
        # if you don’t have listing lat/lon, omit; we’ll fallback to property.location
        # "location": {"lat": 51.676, "lon": -0.607},
        "url": "https://example.com/listing/abc123",
        "media_urls": ["https://example.com/listing/abc123/photo1.jpg"],
    }


def fetch_property(client: OpenSearch, properties_index: str, property_id: str) -> Optional[Dict[str, Any]]:
    try:
        res = client.get(index=properties_index, id=property_id, ignore=[404])
        if res.get("found"):
            return res.get("_source")
    except Exception:
        pass
    return None


def enrich_with_property(listing: Dict[str, Any], prop: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge denormalized fields from the property document into the listing doc."""
    out = dict(listing)
    if prop:
        latest = (prop.get("latest_epc") or {})
        out.setdefault("main_fuel", latest.get("main_fuel"))
        out.setdefault("solar_panels", latest.get("solar_panels"))
        out.setdefault("solar_water_heating", latest.get("solar_water_heating"))
        out.setdefault("epc_rating", latest.get("rating"))
        out.setdefault("epc_score", latest.get("score"))

        # Running cost: prefer property precomputed estimate if present
        if "running_cost_annual" not in out and prop.get("estimated_running_cost"):
            try:
                out["running_cost_annual"] = float(prop["estimated_running_cost"])  # type: ignore
                out["running_cost_monthly"] = round(out["running_cost_annual"] / 12.0, 2)
            except Exception:
                pass

        # Location fallback from property if listing lacks precise lat/lon
        if "location" not in out and prop.get("location"):
            out["location"] = prop["location"]

    return out


def upsert_listings(
    client: OpenSearch,
    listings_index: str,
    properties_index: str,
    batch_size: int = 500,
) -> int:
    actions: List[Dict[str, Any]] = []
    total = 0

    for raw in iter_listings():
        listing_id = raw.get("listing_id")
        property_id = raw.get("property_id")
        if not listing_id or not property_id:
            continue

        prop = fetch_property(client, properties_index, property_id)
        doc = enrich_with_property(raw, prop)

        actions.append(
            {
                "_op_type": "index",  # idempotent with deterministic id
                "_index": listings_index,
                "_id": listing_id,
                "_source": doc,
            }
        )

        if len(actions) >= batch_size:
            helpers.bulk(client, actions)
            total += len(actions)
            actions = []

    if actions:
        helpers.bulk(client, actions)
        total += len(actions)

    return total


def main():
    parser = argparse.ArgumentParser(description="Ingest sample listings with enrichment")
    parser.add_argument("--opensearch-url", default=os.environ.get("OPENSEARCH_URL", "http://localhost:9200"))
    parser.add_argument("--user", default=os.environ.get("OPENSEARCH_USER"))
    parser.add_argument("--password", default=os.environ.get("OPENSEARCH_PASS"))
    parser.add_argument("--properties-index", default=os.environ.get("PROPERTIES_INDEX", "properties"))
    parser.add_argument("--listings-index", default=os.environ.get("LISTINGS_INDEX", "listings-v1"))
    args = parser.parse_args()

    client = OpenSearch(
        [args.opensearch_url],
        http_auth=(args.user, args.password) if args.user else None,
        use_ssl=args.opensearch_url.startswith("https"),
        verify_certs=False,
        ssl_show_warn=False,
    )

    total = upsert_listings(client, args.listings_index, args.properties_index)
    print(f"Upserted {total} listings into {args.listings_index}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from fastapi import FastAPI, Query, Request, Response
from fastapi import HTTPException
from typing import List, Dict, Any, Optional
from fastapi.middleware.cors import CORSMiddleware
import math
import os
import httpx
from opensearchpy import OpenSearch
import logging

# optionally load a local .env file for development; secrets should not be committed
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=False)

# Import running cost calculation
from running_cost import calculate_running_cost


# We return upstream EPC data as-is; do not rename or map fields.

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("green-home-search.api")

# OpenSearch configuration
OPENSEARCH_URL = os.environ.get("OPENSEARCH_URL", "http://localhost:9200")
OPENSEARCH_USER = os.environ.get("OPENSEARCH_USER", "admin")
OPENSEARCH_PASS = os.environ.get("OPENSEARCH_PASS", "admin")
CERTIFICATES_INDEX = os.environ.get("CERTIFICATES_INDEX", "certificates")
PROPERTIES_INDEX = os.environ.get("PROPERTIES_INDEX", "properties")
LISTINGS_SEARCH_ALIAS = os.environ.get("LISTINGS_SEARCH_ALIAS", "listings-active")

# Initialize OpenSearch client
opensearch_client = OpenSearch(
    hosts=[OPENSEARCH_URL],
    http_auth=(OPENSEARCH_USER, OPENSEARCH_PASS) if OPENSEARCH_USER and OPENSEARCH_PASS else None,
    use_ssl=False,
    verify_certs=False,
    ssl_assert_hostname=False,
    ssl_show_warn=False
)

app = FastAPI(title="Green Home Search API")

# Allow calls from the Vite dev server and local clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", summary="API root")
async def root():
    return {"status": "ok", "message": "Green Home Search API - see /docs"}


@app.post("/running-cost", summary="Calculate running cost from EPC document")
async def get_running_cost(epc_document: Dict[str, Any]):
    """
    Calculate monthly running cost based on EPC rating.
    
    Parameters:
    - epc_document: An EPC document with a 'current-energy-rating' or 'CURRENT_ENERGY_RATING' field
    
    Returns:
    - running_cost: Monthly running cost in GBP, or null if rating is invalid
    
    Example request body:
    ```json
    {
        "current-energy-rating": "C"
    }
    ```
    
    Example response:
    ```json
    {
        "running_cost": 100
    }
    ```
    """
    cost = calculate_running_cost(epc_document)
    return {"running_cost": cost}


@app.get("/health", summary="Health check with index statistics")
async def health():
    """Get API health status and OpenSearch index statistics."""
    try:
        # Check OpenSearch connectivity
        cluster_health = opensearch_client.cluster.health()
        
        # Get index statistics
        cert_stats = opensearch_client.count(index=CERTIFICATES_INDEX)
        
        return {
            "status": "healthy",
            "opensearch": {
                "cluster_status": cluster_health.get("status"),
                "certificates_count": cert_stats["count"]
            },
            "indices": {
                "certificates": CERTIFICATES_INDEX
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.get("/search", summary="Search places by address")
async def search(
    request: Request,
    response: Response,
    address: str = Query(..., description="Address or place to search for (example: 'High Wycombe')"),
    limit: int = Query(20, description="Maximum number of results to return", ge=1, le=100),
    offset: int = Query(0, description="Number of results to skip for pagination", ge=0),
    energy_rating: Optional[str] = Query(None, description="Filter by energy rating (A, B, C, D, E, F, G)"),
    property_type: Optional[str] = Query(None, description="Filter by property type (House, Flat, etc.)"),
    min_efficiency: Optional[int] = Query(None, description="Minimum energy efficiency score", ge=0, le=100),
    max_efficiency: Optional[int] = Query(None, description="Maximum energy efficiency score", ge=0, le=100),
    sort_by: Optional[str] = Query(None, description="Sort results by: relevance (default), rating, running_cost"),
):
    """
    Parameters:
    - address: query string
    - limit: maximum number of results (1-100)
    - offset: number of results to skip for pagination
    - energy_rating: optional filter by energy rating
    - property_type: optional filter by property type
    - min_efficiency: minimum energy efficiency score
    - max_efficiency: maximum energy efficiency score
    - sort_by: sort results by 'relevance' (default), 'rating', or 'running_cost'

    Returns a list of properties from the opensearch-epc db matching the address query.
    """
    # Log incoming request
    try:
        client_ip = request.client.host
    except Exception:
        client_ip = None
    logger.info("/search called address=%s client=%s limit=%d", address, client_ip, limit)

    try:
        # Build the optimized search query
        query = build_optimized_search_query(
            address, energy_rating, property_type, min_efficiency, max_efficiency
        )
        
        # Build sort clause based on sort_by parameter
        sort_clause = build_sort_clause(sort_by)
        
        # Execute the search with optimizations
        search_body = {
            "query": query,
            "from": offset,
            "size": limit,
            "sort": sort_clause,
            "_source": get_source_fields(),
            "track_total_hits": True,
            "timeout": "10s"  # Add timeout to prevent long-running queries
        }
        
        result = opensearch_client.search(
            index=CERTIFICATES_INDEX,
            body=search_body,
            request_timeout=30
        )
        
        # Process and format the results
        properties = []
        for hit in result['hits']['hits']:
            source = hit['_source']
            property_data = {
                "id": source.get('LMK_KEY'),
                "address": format_address(source),
                "postcode": source.get('POSTCODE'),
                "uprn": source.get('UPRN'),
                "current_energy_rating": source.get('CURRENT_ENERGY_RATING'),
                "potential_energy_rating": source.get('POTENTIAL_ENERGY_RATING'),
                "current_energy_efficiency": source.get('CURRENT_ENERGY_EFFICIENCY'),
                "potential_energy_efficiency": source.get('POTENTIAL_ENERGY_EFFICIENCY'),
                "property_type": source.get('PROPERTY_TYPE'),
                "built_form": source.get('BUILT_FORM'),
                "lodgement_date": source.get('LODGEMENT_DATE'),
                "total_floor_area": source.get('TOTAL_FLOOR_AREA'),
                "energy_consumption_current": source.get('ENERGY_CONSUMPTION_CURRENT'),
                "co2_emissions_current": source.get('CO2_EMISSIONS_CURRENT'),
                "heating_cost_current": source.get('HEATING_COST_CURRENT'),
                "hot_water_cost_current": source.get('HOT_WATER_COST_CURRENT'),
                "lighting_cost_current": source.get('LIGHTING_COST_CURRENT'),
                "construction_age_band": source.get('CONSTRUCTION_AGE_BAND'),
                "tenure": source.get('TENURE'),
                "main_fuel": source.get('MAIN_FUEL'),
                "score": hit['_score'],
                "running_cost": calculate_running_cost(source)
            }
            properties.append(property_data)
        
        return {
            "query": address,
            "total": result['hits']['total']['value'],
            "took": result['took'],
            "offset": offset,
            "limit": limit,
            "index_used": CERTIFICATES_INDEX,
            "results": properties
        }
        
    except Exception as e:
        logger.error("Search error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")




def build_sort_clause(sort_by: Optional[str] = None) -> List[Dict[str, Any]]:
    """Build OpenSearch sort clause based on sort_by parameter.
    
    Args:
        sort_by: Sort option - 'relevance', 'rating', or 'running_cost'
        
    Returns:
        List of sort clauses for OpenSearch
    """
    # Define energy rating order (A is best, G is worst)
    rating_order = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7}
    
    if sort_by == "rating":
        # Sort by energy rating (A to G), then by score
        # Use a script to map ratings to numeric values for proper sorting
        return [
            {
                "_script": {
                    "type": "number",
                    "script": {
                        "lang": "painless",
                        "source": """
                            String rating = doc['CURRENT_ENERGY_RATING.keyword'].size() > 0 ? 
                                doc['CURRENT_ENERGY_RATING.keyword'].value : 'Z';
                            Map ratings = ['A':1, 'B':2, 'C':3, 'D':4, 'E':5, 'F':6, 'G':7];
                            return ratings.getOrDefault(rating, 999);
                        """
                    },
                    "order": "asc"
                }
            },
            {"_score": {"order": "desc"}}
        ]
    elif sort_by == "running_cost":
        # Sort by running cost (low to high), then by score
        # We need to calculate running cost in the script since it's computed
        return [
            {
                "_script": {
                    "type": "number",
                    "script": {
                        "lang": "painless",
                        "source": """
                            if (doc['HEATING_COST_CURRENT'].size() > 0 && doc['HOT_WATER_COST_CURRENT'].size() > 0) {
                                return doc['HEATING_COST_CURRENT'].value + doc['HOT_WATER_COST_CURRENT'].value;
                            }
                            return 999999;
                        """
                    },
                    "order": "asc"
                }
            },
            {"_score": {"order": "desc"}}
        ]
    else:
        # Default: sort by relevance (score) then by lodgement date
        return [
            {"_score": {"order": "desc"}},
            {"LODGEMENT_DATETIME": {"order": "desc", "missing": "_last"}}
        ]


def build_optimized_search_query(
    address: str, 
    energy_rating: Optional[str] = None, 
    property_type: Optional[str] = None,
    min_efficiency: Optional[int] = None,
    max_efficiency: Optional[int] = None,
) -> Dict[str, Any]:
    """Build optimized OpenSearch query for postcode search with filters."""
    
    # Normalize the postcode input (uppercase, handle spacing)
    normalized_postcode = address.upper().strip()
    
    # Handle different postcode formats (with or without space)
    postcode_variants = [normalized_postcode]
    if ' ' in normalized_postcode:
        # If space exists, also try without space
        postcode_variants.append(normalized_postcode.replace(' ', ''))
    else:
        # If no space, try to add space in typical UK postcode format
        # UK postcodes are typically: 1-2 letters, 1-2 digits, optional letter, space, 1 digit, 2 letters
        import re
        # Try to insert space before last 3 characters if it looks like a postcode
        if len(normalized_postcode) >= 5 and re.match(r'^[A-Z]{1,2}\d{1,2}[A-Z]?\d[A-Z]{2}$', normalized_postcode):
            postcode_with_space = normalized_postcode[:-3] + ' ' + normalized_postcode[-3:]
            postcode_variants.append(postcode_with_space)

    address_query = {
        "bool": {
            "should": [
                # Exact term match on keyword field (highest priority)
                {
                    "terms": {
                        "POSTCODE.keyword": postcode_variants,
                        "boost": 10
                    }
                },
                # Exact phrase match on analyzed field (case-insensitive)
                {
                    "bool": {
                        "should": [
                            {
                                "match_phrase": {
                                    "POSTCODE": {
                                        "query": variant,
                                        "boost": 8
                                    }
                                }
                            } for variant in postcode_variants
                        ]
                    }
                }
            ],
            "minimum_should_match": 1
        }
    }
    
    # Build filters for certificates index
    filters = []
    if energy_rating:
        filters.append({
            "term": {
                "CURRENT_ENERGY_RATING.keyword": energy_rating.upper()
            }
        })
    
    if property_type:
        filters.append({
            "term": {
                "PROPERTY_TYPE.keyword": property_type
            }
        })
    
    if min_efficiency is not None or max_efficiency is not None:
        range_filter = {"range": {"CURRENT_ENERGY_EFFICIENCY": {}}}
        if min_efficiency is not None:
            range_filter["range"]["CURRENT_ENERGY_EFFICIENCY"]["gte"] = min_efficiency
        if max_efficiency is not None:
            range_filter["range"]["CURRENT_ENERGY_EFFICIENCY"]["lte"] = max_efficiency
        filters.append(range_filter)
    
    if filters:
        return {
            "bool": {
                "must": [address_query],
                "filter": filters
            }
        }
    else:
        return address_query


def get_source_fields() -> Dict[str, List[str]]:
    """Get optimized source fields based on index type."""
    return {
        "includes": [
            "LMK_KEY", "ADDRESS1", "ADDRESS2", "ADDRESS3", "POSTCODE", "UPRN",
            "CURRENT_ENERGY_RATING", "POTENTIAL_ENERGY_RATING", "CURRENT_ENERGY_EFFICIENCY",
            "POTENTIAL_ENERGY_EFFICIENCY", "PROPERTY_TYPE", "BUILT_FORM", "LODGEMENT_DATE",
            "TOTAL_FLOOR_AREA", "ENERGY_CONSUMPTION_CURRENT", "CO2_EMISSIONS_CURRENT",
            "HEATING_COST_CURRENT", "HOT_WATER_COST_CURRENT", "LIGHTING_COST_CURRENT",
            "CONSTRUCTION_AGE_BAND", "TENURE", "MAIN_FUEL"
        ],
        "excludes": [
            "*_DESCRIPTION", "*_ENV_EFF", "*_ENERGY_EFF", "RECOMMENDATIONS_*"
        ]
    }


def format_address(source: Dict[str, Any]) -> str:
    """Format address from source document."""
    address_parts = []
    for field in ['ADDRESS1', 'ADDRESS2', 'ADDRESS3']:
        value = source.get(field)
        if value and value.strip():
            address_parts.append(value.strip())
    
    address = ', '.join(address_parts)
    postcode = source.get('POSTCODE')
    if postcode and postcode.strip():
        address += f', {postcode.strip()}'
    
    return address


# ---------------------------
# Listings search endpoints
# ---------------------------




def build_listings_sort_clause(sort_by: Optional[str] = None) -> List[Dict[str, Any]]:
    """Build OpenSearch sort clause for listings based on sort_by parameter.
    
    Args:
        sort_by: Sort option - 'price' (default), 'rating', or 'running_cost'
        
    Returns:
        List of sort clauses for OpenSearch
    """
    if sort_by == "rating":
        # Sort by EPC rating (A to G), then by price
        return [
            {
                "_script": {
                    "type": "number",
                    "script": {
                        "lang": "painless",
                        "source": """
                            String rating = doc['epc_rating'].size() > 0 ? 
                                doc['epc_rating'].value : 'Z';
                            Map ratings = ['A':1, 'B':2, 'C':3, 'D':4, 'E':5, 'F':6, 'G':7];
                            return ratings.getOrDefault(rating, 999);
                        """
                    },
                    "order": "asc"
                }
            },
            {"price": {"order": "asc", "missing": "_last"}},
            {"listed_at": {"order": "desc"}}
        ]
    elif sort_by == "running_cost":
        # Sort by running cost (low to high), then by price
        return [
            {"running_cost_monthly": {"order": "asc", "missing": "_last"}},
            {"price": {"order": "asc", "missing": "_last"}},
            {"listed_at": {"order": "desc"}}
        ]
    else:
        # Default: sort by price then by listing date
        return [
            {"price": {"order": "asc", "missing": "_last"}},
            {"listed_at": {"order": "desc"}}
        ]


def build_listings_query(
    q: Optional[str],
    lat: Optional[float],
    lon: Optional[float],
    radius_km: Optional[float],
    bedrooms_min: Optional[int],
    main_fuel: Optional[List[str]],
    solar_panels: Optional[bool],
    solar_water_heating: Optional[bool],
    running_cost_monthly_max: Optional[float],
) -> Dict[str, Any]:
    filters: List[Dict[str, Any]] = [{"term": {"is_active": True}}]

    # Location filter
    if lat is not None and lon is not None and radius_km is not None:
        filters.append(
            {
                "geo_distance": {
                    "distance": f"{radius_km}km",
                    "location": {"lat": lat, "lon": lon},
                }
            }
        )

    # Bedrooms
    if bedrooms_min is not None:
        filters.append({"range": {"bedrooms": {"gte": bedrooms_min}}})

    # Main fuel filter
    if main_fuel:
        filters.append({"terms": {"main_fuel": main_fuel}})

    # Solar flags
    if solar_panels is not None:
        filters.append({"term": {"solar_panels": bool(solar_panels)}})
    if solar_water_heating is not None:
        filters.append({"term": {"solar_water_heating": bool(solar_water_heating)}})

    # Running cost cap
    if running_cost_monthly_max is not None:
        filters.append(
            {"range": {"running_cost_monthly": {"lte": running_cost_monthly_max}}}
        )

    # Text query (postcode/address)
    must: List[Dict[str, Any]] = []
    if q:
        must.append(
            {
                "bool": {
                    "should": [
                        {"term": {"postcode": {"value": q.upper(), "boost": 5}}},
                        {"match": {"address_line": {"query": q, "boost": 2}}},
                    ],
                    "minimum_should_match": 1,
                }
            }
        )

    query: Dict[str, Any] = {"bool": {}}
    if must:
        query["bool"]["must"] = must
    if filters:
        query["bool"]["filter"] = filters

    return query


@app.get("/listings/search", summary="Search property listings")
async def search_listings(
    request: Request,
    response: Response,
    q: Optional[str] = Query(None, description="Address or postcode"),
    lat: Optional[float] = Query(None, description="Latitude for geo search"),
    lon: Optional[float] = Query(None, description="Longitude for geo search"),
    radius_km: Optional[float] = Query(
        10.0, description="Search radius in km when using geo search", ge=0.1, le=200.0
    ),
    bedrooms_min: Optional[int] = Query(None, ge=0),
    main_fuel: Optional[List[str]] = Query(
        None, description="Filter by main fuel types"
    ),
    solar_panels: Optional[bool] = Query(None),
    solar_water_heating: Optional[bool] = Query(None),
    running_cost_monthly_max: Optional[float] = Query(None, ge=0.0),
    collapse_per_property: bool = Query(
        True, description="Collapse multiple listings per property_id"
    ),
    size: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: Optional[str] = Query(None, description="Sort results by: price (default), rating, running_cost"),
):
    """Search active listings by address/postcode or by lat/lon within a radius,
    and filter by bedrooms, main fuel, solar flags, and max monthly running cost.
    Results can be sorted by price (default), rating, or running_cost.
    """
    try:
        query = build_listings_query(
            q=q,
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            bedrooms_min=bedrooms_min,
            main_fuel=main_fuel,
            solar_panels=solar_panels,
            solar_water_heating=solar_water_heating,
            running_cost_monthly_max=running_cost_monthly_max,
        )

        # Build sort clause based on sort_by parameter
        sort_clause = build_listings_sort_clause(sort_by)

        body: Dict[str, Any] = {
            "query": query,
            "from": offset,
            "size": size,
            "sort": sort_clause,
            "track_total_hits": True,
        }

        if collapse_per_property:
            body["collapse"] = {
                "field": "property_id",
                "inner_hits": {
                    "name": "all_listings_for_property",
                    "size": 5,
                    "sort": [{"price": "asc"}],
                },
            }

        result = opensearch_client.search(
            index=LISTINGS_SEARCH_ALIAS, body=body, request_timeout=30
        )

        # Return raw listing docs for now; UI can shape them as needed
        hits = result.get("hits", {}).get("hits", [])
        listings = [{"id": h.get("_id"), **(h.get("_source") or {})} for h in hits]

        return {
            "total": result.get("hits", {}).get("total", {}).get("value", 0),
            "took": result.get("took"),
            "offset": offset,
            "limit": size,
            "index_used": LISTINGS_SEARCH_ALIAS,
            "results": listings,
        }
    except Exception as e:
        logger.error("Listings search error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Listings search failed: {str(e)}")

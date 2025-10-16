from fastapi import FastAPI, Query, Request, Response
from fastapi import HTTPException
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import math
import os
import httpx
# optionally load a local .env file for development; secrets should not be committed
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=False)


# We return upstream EPC data as-is; do not rename or map fields.


import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("green-home-search.api")


app = FastAPI(title="Green Home Search API")

# Allow calls from the Vite dev server and local clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance between two lat/lon points in kilometers."""
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


@app.get("/", summary="API root")
async def root():
    return {"status": "ok", "message": "Green Home Search API - see /docs"}




@app.get("/search", summary="Search places by address")
async def search(
    request: Request,
    response: Response,
    address: str = Query(..., description="Address or place to search for (example: 'High Wycombe')"),
):
    """
    Parameters:
    - address: query string

    Returns a list of properties from the EPC Register matching the address query.
    """
    # Log incoming request
    try:
        client_ip = request.client.host
    except Exception:
        client_ip = None
    logger.info("/search called address=%s client=%s", address, client_ip)

    # default to the official EPC Open Data Communities search endpoint if not overridden
    EPC_API_URL = os.getenv("EPC_API_URL", "https://epc.opendatacommunities.org/api/v1/domestic/search")

    EPC_API_TOKEN = os.getenv("EPC_API_TOKEN")
    
    if not EPC_API_TOKEN:
        logger.error("EPC_API_TOKEN is not configured; refusing to proceed")
        raise HTTPException(status_code=503, detail="EPC API token not configured")

    logger.info("Calling external EPC API %s", EPC_API_URL)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Build headers: include API key and optional auth token if provided
            headers = {"Accept": "application/json"}
            if EPC_API_TOKEN:
                # do NOT log this value
                headers["Authorization"] = f"Basic {EPC_API_TOKEN}"

            resp = await client.get(EPC_API_URL, params={"address": address}, headers=headers)

        logger.info("EPC API responded %s", resp.status_code)

        # Surface upstream non-200 responses as 502 Bad Gateway with upstream body
        if resp.status_code != 200:
            text = resp.text
            logger.error("EPC API returned non-200: %s %s", resp.status_code, text)
            raise HTTPException(status_code=502, detail=f"Upstream EPC API returned {resp.status_code}: {text}")

        payload = resp.json()
        results = payload.get("rows")
        nextSearchAfter = resp.headers.get("x-next-search-after")

        count = len(results) if results else 0
        logger.info("/search returning %d results for address=%s", count, address)

        if nextSearchAfter:
            response.headers["X-Next-Search-After"] = nextSearchAfter

        return results or []
    except httpx.HTTPStatusError as e:
        logger.error("EPC API status error: %s", e)
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.exception("EPC API call failed: %s", e)
        raise HTTPException(status_code=502, detail=str(e))

FastAPI mock API for Green Home Search

Files:
- main.py - FastAPI app with a /search endpoint
- requirements.txt - Python deps

Run locally (recommended in a virtualenv):

# install
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt

# run
uvicorn main:app --reload --port 8000

Endpoints:
- GET /search?address=...  (address is required and will be forwarded to the EPC API)
- GET /  (root)

Notes:
- The API forwards address queries to the EPC Register and returns mapped results. There is no local mock fallback; upstream errors will be returned to the client.
- CORS is enabled for localhost dev servers.

Dev helper
----------
There's a convenience script at `scripts/start-dev.ps1` that opens two PowerShell windows and starts the API (uvicorn).

Run it from the repo root:

```powershell
.\scripts\start-dev.ps1
```

The frontend includes a small debug panel (visible in the search results area) that shows the last request URL and raw response or error message to help debug proxy/routing issues.

EPC API integration
-------------------
You can configure the API to call the UK EPC Register by setting these environment variables in your shell or CI environment (do NOT commit them to source control):

- `EPC_API_KEY` - your private API key
- `EPC_API_URL` - the base URL for the search endpoint (e.g. as documented by the EPC API)

Example (PowerShell):

```powershell
setx EPC_API_KEY "your-secret-key"
setx EPC_API_URL "https://api.example.gov.uk/epc/search"
# restart shell for setx to take effect, or run in-session:
$env:EPC_API_KEY = 'your-secret-key'
$env:EPC_API_URL = 'https://api.example.gov.uk/epc/search'
```

When these are present the API will attempt to call the external service and map returned items into the place model. If the external call fails or returns no candidates we fall back to the local mock data so development can continue offline.

Security note: keep API keys out of version control and use environment variables or a secrets manager. The `scripts/start-dev.ps1` helper does not store keys — it will use the environment of the shell that launches it.

Using a local .env (development)
--------------------------------
You can put your API key and URL into `api/.env` for local development (this repo's `.gitignore` excludes `.env` and `api/.env`). Example `api/.env`:

```
EPC_API_KEY=your-real-key-here
EPC_API_URL=https://epc.opendatacommunities.org/api/v1/domestic/search
EPC_API_TOKEN=base64-encoded-token-if-required
```

The application will load `api/.env` automatically at startup (via python-dotenv). Do not commit this file.
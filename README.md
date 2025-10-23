# Green Home Search

![CI](https://github.com/tbrd/green-home-search/workflows/CI/badge.svg)

A three-tier energy efficiency search platform for UK domestic properties using EPC (Energy Performance Certificate) data.

## Architecture

This project consists of three main components:

- **`opensearch-epc/`** - Data ingestion pipeline for EPC CSV data into OpenSearch cluster
- **`api/`** - FastAPI backend that queries OpenSearch and proxies to external EPC APIs
- **`web/`** - React/TypeScript frontend with Vite dev server and TanStack Query

## Continuous Integration

The project uses GitHub Actions for CI/CD. The workflow automatically:

- **API Tests**: Runs pytest tests against the FastAPI backend with a real OpenSearch instance
- **Web Lint & Build**: Validates TypeScript code with ESLint and builds the production bundle

The CI workflow runs on:
- Push to `main` branch
- Pull requests targeting `main` branch

### Workflow Jobs

#### API Tests
- Sets up Python 3.12
- Starts OpenSearch 2.11.0 service
- Installs Python dependencies
- Creates test index with EPC schema
- Runs pytest test suite

#### Web Lint & Build
- Sets up Node.js 20
- Installs npm dependencies
- Runs ESLint for code quality
- Builds production bundle with Vite

## Development

See individual component READMEs for development setup:
- [API Setup](api/README.md)
- [Web Setup](web/README.md)

## Quick Start

```bash
# 1. Start OpenSearch cluster
cd opensearch-epc && docker-compose up -d

# 2. Start API server
cd api
python -m venv .venv && source .venv/bin/activate  # or .\.venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 3. Start frontend dev server
cd web
npm install && npm run dev  # Runs on :5173 with API proxy
```

## License

See individual component licenses.

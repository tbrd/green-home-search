# Copilot Instructions for Green Home Search

## Project Overview

Green Home Search is a web application for searching UK properties and viewing their Energy Performance Certificate (EPC) ratings. The project consists of:

- **Frontend (web/)**: React + TypeScript + Vite application
- **Backend (api/)**: FastAPI Python application  
- **Data (opensearch-epc/)**: OpenSearch configuration for EPC data indexing

## Architecture

- Frontend runs on Vite dev server (default: http://localhost:5173)
- Backend API runs on uvicorn (default: http://localhost:8000)
- API integrates with the UK EPC Register API for property data
- CORS is configured for local development

## Development Setup

### Prerequisites
- Node.js and npm (for frontend)
- Python 3.x and pip (for backend)
- PowerShell (optional, for convenience scripts)

### Frontend Setup (web/)
```bash
cd web
npm install
npm run dev        # Start dev server
npm run build      # Production build
npm run lint       # Run ESLint
```

### Backend Setup (api/)
```bash
cd api
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Running Tests
```bash
cd api
pytest
```

## Code Style and Conventions

### TypeScript/React (Frontend)
- Use TypeScript for all new files
- Follow React hooks best practices
- Use TanStack Query (@tanstack/react-query) for API data fetching
- Component files use `.tsx` extension
- Keep components in `web/src/components/`
- API queries in `web/src/queries/`
- Run `npm run lint` before committing

### Python (Backend)
- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- FastAPI endpoints should include docstrings with parameter descriptions
- Use async/await for I/O operations
- Run pytest for testing

### General
- Use meaningful variable and function names
- Keep functions focused and single-purpose
- Add comments only when necessary to explain complex logic

## Testing Requirements

### Backend Tests
- Tests are in `api/tests/`
- Use pytest framework
- Test file naming: `test_*.py`
- Mock external API calls where appropriate
- Ensure all endpoints have test coverage

### Frontend Tests
- Currently no test framework configured
- When adding tests, follow React Testing Library patterns
- Test user interactions and component rendering

## Security Considerations

### API Keys and Secrets
- **NEVER commit API keys or secrets to source control**
- Use environment variables for sensitive data:
  - `EPC_API_TOKEN`: Base64 encoded auth token for EPC API
  - `EPC_API_URL`: EPC API endpoint URL
- Use `api/.env` file for local development (already in .gitignore)
- Example `.env` setup in `api/README.md`

### CORS Configuration
- CORS is configured for local development in `api/main.py`
- Review CORS settings before production deployment
- Do not use wildcard (`*`) origins in production

### Input Validation
- All API endpoints should validate input parameters
- Use FastAPI's Query/Path validators
- Sanitize user inputs before forwarding to external APIs

## API Integration

### EPC Register API
- Backend forwards address queries to UK EPC Register API
- Requires `EPC_API_TOKEN` environment variable
- Returns 503 error if token not configured
- Returns 502 error if upstream API fails
- Response includes `X-Next-Search-After` header for pagination

### Error Handling
- Handle upstream API errors gracefully
- Log all API calls and errors
- Return appropriate HTTP status codes
- Include helpful error messages in responses

## File Organization

```
├── .github/               # GitHub configuration
├── api/                   # FastAPI backend
│   ├── main.py           # Main API application
│   ├── requirements.txt  # Python dependencies
│   └── tests/            # Backend tests
├── web/                   # React frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── queries/      # TanStack Query definitions
│   │   ├── App.tsx       # Main app component
│   │   └── main.tsx      # Entry point
│   ├── package.json      # Node dependencies
│   └── vite.config.ts    # Vite configuration
├── opensearch-epc/       # OpenSearch configuration
└── scripts/              # Development helper scripts
```

## Common Tasks

### Adding a New API Endpoint
1. Add endpoint function in `api/main.py`
2. Include docstring with parameters description
3. Add type hints for parameters and return value
4. Add corresponding test in `api/tests/`
5. Update CORS settings if needed
6. Document in API readme

### Adding a New React Component
1. Create component file in `web/src/components/`
2. Use TypeScript and functional components
3. Follow existing component patterns
4. Import and use in parent components
5. Add appropriate prop types

### Updating Dependencies
1. **Backend**: Update `api/requirements.txt` and run `pip install -r requirements.txt`
2. **Frontend**: Update `web/package.json` and run `npm install`
3. Test thoroughly after updates
4. Check for security vulnerabilities

## Debugging

### Frontend Debug Panel
- A debug panel is included in the search results area
- Shows last request URL and raw response
- Helps debug proxy/routing issues
- Visible during development

### Backend Logging
- Application uses Python logging module
- Log level: INFO
- Logs include timestamps, level, and logger name
- All API calls are logged with parameters
- Errors include full exception details

## Git Workflow

- Work on feature branches
- Write clear commit messages
- Keep commits focused and atomic
- Do not commit `.env` files or secrets
- Run linters and tests before pushing

## Additional Resources

- FastAPI documentation: https://fastapi.tiangolo.com/
- React documentation: https://react.dev/
- Vite documentation: https://vite.dev/
- TanStack Query: https://tanstack.com/query/
- UK EPC Register: https://epc.opendatacommunities.org/

## Questions or Issues?

When working on this codebase:
- Review existing code patterns before implementing new features
- Check both API and web README files for specific setup instructions
- Ensure all environment variables are properly configured
- Test both frontend and backend components after changes

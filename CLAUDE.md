# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

**gl-mcp-python** is the Python/FastAPI implementation of the Godfrey Labs MCP Server, replacing the TypeScript version (gl-mcp-node) to leverage the Python AI/ML ecosystem.

## Tech Stack

- **Framework**: FastAPI
- **Python**: 3.11+
- **Package Manager**: uv (for fast dependency management)
- **MCP SDK**: Official Anthropic Python SDK (`mcp` package)
- **Auth**: Keycloak OAuth with JWT validation
- **Database**: PostgreSQL (asyncpg)
- **Deployment**: AWS ECS

## Project Structure

```
gl-mcp-python/
├── src/gl_mcp/
│   ├── __init__.py
│   ├── main.py           # FastAPI app entrypoint
│   ├── config.py         # Pydantic settings
│   ├── providers/        # MCP tool providers
│   │   ├── __init__.py
│   │   ├── news.py       # GL News provider (TODO)
│   │   ├── jira.py       # JIRA provider (TODO)
│   │   ├── vault.py      # Vault provider (TODO)
│   │   └── admin.py      # Admin provider (TODO)
│   ├── auth/             # Keycloak auth (TODO)
│   └── mcp/              # MCP protocol (TODO)
├── tests/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── CLAUDE.md
```

## Common Commands

```bash
# Install dependencies
uv pip install -e ".[dev]"

# Run locally
uvicorn gl_mcp.main:app --reload --port 3000

# Run with Docker
docker-compose up --build

# Run tests
pytest tests/ -v

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Environment Variables

Copy `.env.example` to `.env` and fill in the values. Key variables:

- `JIRA_*`: JIRA API credentials
- `GLNEWS_DB_*`: GL News PostgreSQL connection
- `GLCHAT_DB_*`: GL Chat PostgreSQL connection  
- `KEYCLOAK_*`: Keycloak OAuth configuration
- `AUTH_ENABLED`: Set to `true` to enable authentication

## Migration Status (from gl-mcp-node)

- [x] Project scaffold
- [x] Health check endpoint
- [ ] MCP protocol implementation (GL-273)
- [ ] Keycloak OAuth integration (GL-274)
- [ ] News provider
- [ ] JIRA provider
- [ ] Vault provider
- [ ] Admin provider
- [ ] ECS deployment (GL-279)

## Related JIRA Tickets

- GL-270: Epic - gl-mcp Python Migration
- GL-271: Project setup (this repo)
- GL-273: MCP protocol implementation
- GL-274: Keycloak OAuth integration
- GL-279: ECS deployment setup
- GL-280: Testing and cutover

## Reference

- TypeScript implementation: https://github.com/GodfreySolutions/gl-mcp-node
- MCP Python SDK: https://github.com/anthropics/mcp-python
- Keycloak: https://identity.godfreylabs.com

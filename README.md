# gl-mcp-python

Godfrey Labs MCP Server - Python/FastAPI implementation with AI/ML capabilities.

## Overview

This is a Python reimplementation of the gl-mcp server, migrating from TypeScript/Node to Python/FastAPI to better leverage the AI/ML ecosystem.

## Quick Start

```bash
# Install dependencies
uv pip install -e ".[dev]"

# Run locally
uvicorn gl_mcp.main:app --reload --port 3000

# Run with Docker
docker-compose up --build
```

## Documentation

See [CLAUDE.md](./CLAUDE.md) for detailed project documentation.

## Related

- GL-270: Epic - gl-mcp Python Migration
- Original TypeScript implementation: gl-mcp-node

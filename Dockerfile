FROM python:3.11-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml .

# Install dependencies
RUN uv pip install --system --no-cache -e .

# Copy application code
COPY src/ src/

# Expose port
EXPOSE 3000

# Run the application
CMD ["uvicorn", "gl_mcp.main:app", "--host", "0.0.0.0", "--port", "3000"]

# Multi-Stage Production Dockerfile for Autonomous Python Agents
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final Production Runner Stage
FROM python:3.12-slim AS runner

WORKDIR /app

# Security: Create non-root user
RUN useradd -m -u 1000 agentuser

# Copy installed packages from builder
COPY --from=builder /root/.local /home/agentuser/.local
ENV PATH=/home/agentuser/.local/bin:$PATH

# Copy application code
COPY --chown=agentuser:agentuser . /app

USER agentuser

# Expose FastAPI HTTP Port
EXPOSE 8000

# Production Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Launch production server with Uvicorn
CMD ["uvicorn", "chapter_09_production_deployment:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

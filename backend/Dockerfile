FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim AS production

WORKDIR /app

# Create non-root user
RUN addgroup --system --gid 1000 appgroup && \
    adduser --system --uid 1000 --gid 1000 --disabled-password --gecos "" appuser

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy application code
COPY backend/ ./backend/
COPY pyproject.toml ./
COPY README.md ./
COPY VERSION ./

# Create data directory and set permissions
RUN mkdir -p /data && chown -R appuser:appgroup /data /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
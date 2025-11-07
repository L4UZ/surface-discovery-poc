# Multi-stage Dockerfile for Surface Discovery
# Stage 1: Build Go-based security tools
FROM golang:1.24-bookworm AS go-builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    gcc \
    libpcap-dev \
    && rm -rf /var/lib/apt/lists/*

# Install ProjectDiscovery tools (separate RUN commands for better caching and retry)
RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
RUN go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
RUN go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
RUN go install -v github.com/projectdiscovery/katana/cmd/katana@latest
RUN go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
RUN go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest

# Stage 2: Runtime image
FROM python:3.11-slim

# Metadata
LABEL maintainer="surface-discovery"
LABEL description="In-depth web attack surface discovery service"
LABEL version="0.1.0"

# Install runtime dependencies including Playwright browser dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libcap2-bin \
    libpcap0.8 \
    && rm -rf /var/lib/apt/lists/*

# Copy Go tools from builder stage
COPY --from=go-builder /go/bin/* /usr/local/bin/

# Set capabilities for naabu (port scanning)
RUN setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip /usr/local/bin/naabu

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create app directory
WORKDIR /app

# Copy dependency files first (for layer caching)
COPY pyproject.toml .

# Install Python dependencies using uv
RUN uv sync --no-dev --frozen

# Install Playwright and Chromium browser (Phase 0: Deep URL Discovery)
# Note: This adds ~300MB to the image size but enables JavaScript execution for SPAs
RUN uv run playwright install chromium --with-deps

# Copy application code
COPY discovery/ ./discovery/
COPY cli.py .

# Create output directory
RUN mkdir -p /output && chmod 777 /output

# Copy entrypoint script
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Use non-root user for security (except for naabu which needs caps)
RUN useradd -m -u 1000 discovery && \
    chown -R discovery:discovery /app /output

# Switch to non-root user
USER discovery

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command (can be overridden)
CMD ["--help"]

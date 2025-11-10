# Surface Discovery - Dockerfile
# Multi-stage build for Node.js/TypeScript implementation

# Stage 1: Build Go tools
FROM golang:1.24-bookworm AS go-builder

# Install build dependencies for naabu (requires libpcap)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpcap-dev \
    && rm -rf /var/lib/apt/lists/*

# Install ProjectDiscovery tools
RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest && \
    go install -v github.com/projectdiscovery/katana/cmd/katana@latest && \
    go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest && \
    go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest

# Stage 2: Runtime
FROM node:20-slim

# Install system dependencies for Playwright and naabu
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    libcap2-bin \
    libpcap0.8 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy Go tools from builder
COPY --from=go-builder /go/bin/* /usr/local/bin/

# Set capabilities for naabu (port scanning)
RUN setcap cap_net_raw,cap_net_admin+eip /usr/local/bin/naabu

# Create non-root user
RUN useradd -m discovery && \
    mkdir -p /app /output && \
    chown -R discovery:discovery /app /output

# Set working directory
WORKDIR /app

# Copy package files
COPY --chown=discovery:discovery package.json pnpm-lock.yaml ./

# Install pnpm and dependencies
RUN corepack enable && \
    corepack prepare pnpm@latest --activate && \
    su discovery -c "pnpm install --frozen-lockfile"

# Install Playwright browsers
RUN su discovery -c "pnpm exec playwright install chromium"

# Copy application source
COPY --chown=discovery:discovery . .

# Build TypeScript
RUN su discovery -c "pnpm run build"

# Switch to non-root user
USER discovery

# Set output volume
VOLUME ["/output"]

# Entry point
ENTRYPOINT ["node", "dist/cli.js"]
CMD ["--help"]

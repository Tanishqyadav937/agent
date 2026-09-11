# Multi-stage build for production deployment to Render
# Stage 1: Build Piper TTS from source
FROM python:3.11-slim as piper-builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    libsndfile1-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone and build Piper
WORKDIR /tmp/piper-build
RUN git clone https://github.com/rhasspy/piper.git . && \
    cd src/python && \
    pip install --no-cache-dir -e . && \
    cd ../.. && \
    mkdir -p /piper-dist && \
    cp -r src/python /piper-dist/

# Download voice model (en_US-lessac-medium) directly from Hugging Face
# This is the stable, canonical source for Piper voice models
RUN mkdir -p /piper-voices && \
    curl -L -o /piper-voices/en_US-lessac-medium.onnx \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx" && \
    curl -L -o /piper-voices/en_US-lessac-medium.onnx.json \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"

# Stage 2: Production runtime
FROM node:20-slim

# Install runtime dependencies (minimal)
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install Node dependencies (production only, no dev)
RUN npm ci --omit=dev

# Copy Piper from builder stage
COPY --from=piper-builder /piper-voices /app/piper-voices
COPY --from=piper-builder /piper-dist /app/piper-dist

# Install Piper TTS in runtime environment
RUN pip install --no-cache-dir piper-tts

# Create piper-venv structure compatible with server.js
RUN mkdir -p /app/piper-venv/bin && \
    ln -s /usr/bin/python3 /app/piper-venv/bin/python

# Copy application code
COPY server.js tools.js .env.example /app/
COPY avatar.html index.html test.html /app/
COPY scripts/ /app/scripts/

# Expose port (Render will set actual port via PORT env var)
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-3000}/health || exit 1

# Set production environment
ENV NODE_ENV=production
ENV LLM_PROVIDER=gemini

# Start application
CMD ["node", "server.js"]

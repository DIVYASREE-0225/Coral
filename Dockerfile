# syntax=docker/dockerfile:1.6
#
# GigProof backend — multi-stage build.
# Stage 1: download the Coral CLI Linux binary.
# Stage 2: install Python deps into a slim runtime.

FROM debian:bookworm-slim AS coral-fetch
ARG CORAL_VERSION=0.3.0
ARG TARGETARCH
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates tar \
    && rm -rf /var/lib/apt/lists/*
# Map docker arch to coral release naming. Coral publishes x86_64 + aarch64.
RUN case "${TARGETARCH}" in \
        amd64) ARCH=x86_64 ;; \
        arm64) ARCH=aarch64 ;; \
        *) echo "unsupported arch ${TARGETARCH}"; exit 1 ;; \
    esac && \
    curl -fsSL "https://github.com/withcoral/coral/releases/download/v${CORAL_VERSION}/coral-${ARCH}-unknown-linux-gnu.tar.gz" \
      -o /tmp/coral.tar.gz && \
    tar -xzf /tmp/coral.tar.gz -C /tmp && \
    install -m 0755 /tmp/coral /usr/local/bin/coral && \
    /usr/local/bin/coral --version


FROM python:3.11-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY --from=coral-fetch /usr/local/bin/coral /usr/local/bin/coral

COPY backend/requirements.txt ./
RUN pip install -r requirements.txt

COPY backend/ ./backend/
COPY coral_sources/ ./coral_sources/

# Install all source specs at image-build time so the container is self-contained.
# Data CSVs are mounted at runtime (see compose volumes).
RUN coral source add --file coral_sources/gigproof.yaml && \
    coral source add --file coral_sources/zomato.yaml && \
    coral source add --file coral_sources/swiggy.yaml && \
    coral source add --file coral_sources/ola.yaml && \
    coral source add --file coral_sources/uber.yaml && \
    coral source add --file coral_sources/urbancompany.yaml || true

WORKDIR /app/backend
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

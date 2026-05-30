# syntax=docker/dockerfile:1.6

FROM python:3.10-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 
PYTHONUNBUFFERED=1 
PIP_DISABLE_PIP_VERSION_CHECK=1 
PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends 
curl 
ca-certificates 
tar 
&& rm -rf /var/lib/apt/lists/*

ARG CORAL_VERSION=0.3.0

RUN curl -fsSL 
https://github.com/withcoral/coral/releases/download/v${CORAL_VERSION}/coral-x86_64-unknown-linux-gnu.tar.gz 
-o /tmp/coral.tar.gz && 
tar -xzf /tmp/coral.tar.gz -C /tmp && 
install -m 0755 /tmp/coral /usr/local/bin/coral

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ ./backend/
COPY coral_sources/ ./coral_sources/

RUN coral source add --file coral_sources/gigproof.yaml || true
RUN coral source add --file coral_sources/zomato.yaml || true
RUN coral source add --file coral_sources/swiggy.yaml || true
RUN coral source add --file coral_sources/ola.yaml || true
RUN coral source add --file coral_sources/uber.yaml || true
RUN coral source add --file coral_sources/urbancompany.yaml || true

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

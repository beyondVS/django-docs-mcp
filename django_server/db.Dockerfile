# PostgreSQL 18 with pgvector and pg_search (ParadeDB)
FROM pgvector/pgvector:pg18

# Install dependencies for ParadeDB repository setup
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Add ParadeDB repository
RUN curl -s https://packagecloud.io/install/repositories/paradedb/pldb/script.deb.sh | bash

# Install pg_search
# Note: ParadeDB might take some time to support the latest PG versions.
# If this fails, consider reverting to PG17 or building from source.
RUN apt-get update && apt-get install -y \
    postgresql-18-pg-search \
    && rm -rf /var/lib/apt/lists/*

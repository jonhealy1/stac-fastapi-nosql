FROM python:3.10-slim


# update apt pkgs, and install build-essential for ciso8601
RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y build-essential git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# update certs used by Requests
ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -e ./stac_fastapi/core
RUN pip install --no-cache-dir -e ./stac_fastapi/elasticsearch[dev,server,serverless_es]

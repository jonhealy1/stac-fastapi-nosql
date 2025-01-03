FROM python:3.10-slim


# update apt pkgs, and install build-essential for ciso8601
RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get -y install build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get -y install git
# update certs used by Requests
ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -e ./stac_fastapi/core
RUN pip install --no-cache-dir -e ./stac_fastapi/opensearch[dev,server]

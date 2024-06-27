FROM python:3.11-slim-bookworm
LABEL org.opencontainers.image.source=https://github.com/kiwix/mirrors-qa
# Copy code
COPY src /src/src
# Copy pyproject.toml and its dependencies
COPY pyproject.toml README.md /src/

# Install + cleanup
RUN pip install --no-cache-dir /src \
 && rm -rf /src

ENV WORKDIR /data
VOLUME /data

ENV WIREGUARD_IMAGE lscr.io/linuxserver/wireguard:latest

VOLUME /var/run/docker.sock

CMD ["mirrors-qa-manager"]

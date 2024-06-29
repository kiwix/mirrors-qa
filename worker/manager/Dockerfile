FROM python:3.11-slim-bookworm
LABEL org.opencontainers.image.source=https://github.com/kiwix/mirrors-qa/worker/manager


COPY src /src/src

COPY pyproject.toml README.md /src/

RUN pip install --no-cache-dir /src \
 && rm -rf /src

RUN mkdir /data

ENV WIREGUARD_IMAGE lscr.io/linuxserver/wireguard:1.0.20210914

CMD ["mirrors-qa-manager", "--help"]

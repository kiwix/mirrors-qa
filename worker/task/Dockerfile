FROM python:3.11-slim-bookworm
LABEL org.opencontainers.image.source=https://github.com/kiwix/mirrors-qa


COPY src /src/src

COPY pyproject.toml README.md /src/

RUN pip install --no-cache-dir /src \
 && rm -rf /src

RUN mkdir /data

CMD ["mirrors-qa-task", "--help"]

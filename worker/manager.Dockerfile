FROM python:3.11-slim-bookworm
LABEL org.opencontainers.image.source=https://github.com/kiwix/mirrors-qa
# Copy code
COPY src /src/src
# Copy pyproject.toml and its dependencies
COPY pyproject.toml README.md /src/

# Install + cleanup
RUN pip install --no-cache-dir /src \
 && rm -rf /src

CMD ["mirrors-qa-worker"]

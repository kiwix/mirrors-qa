ARG PYTHON_VERSION=3.11


FROM python:${PYTHON_VERSION}-slim
LABEL org.opencontainers.image.source=https://github.com/kiwix/mirrors-qa
# Copy code
COPY src /src/src
# Copy pyproject.toml and its dependencies
COPY pyproject.toml README.md /src/

# Install + cleanup
RUN pip install --no-cache-dir /src \
 && rm -rf /src

COPY docker-entrypoint.sh /bin/
RUN chmod +x /bin/docker-entrypoint.sh

ENTRYPOINT ["/bin/docker-entrypoint.sh"]

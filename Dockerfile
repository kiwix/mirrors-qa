ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}-slim
# Copy code
COPY src /src/src
# Copy pyproject.toml and its dependencies
COPY pyproject.toml README.md /src/

# Install + cleanup
RUN pip install --no-cache-dir /src \
 && rm -rf /src

 ENTRYPOINT ["speedtest"]

FROM python:3.11-slim-bookworm
LABEL org.opencontainers.image.source=https://github.com/kiwix/mirrors-qa/backend

RUN apt-get update && apt-get install -y curl

COPY src /src/src

COPY pyproject.toml README.md /src/

RUN pip install --no-cache-dir /src \
 && rm -rf /src

EXPOSE 80

CMD ["uvicorn", "mirrors_qa_backend.main:app", "--host", "0.0.0.0", "--port", "80"]

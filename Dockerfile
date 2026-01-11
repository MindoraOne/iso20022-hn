# Multi-stage build for minimal image size
FROM python:3.9-slim as builder

WORKDIR /build
RUN pip install --no-cache-dir poetry
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-interaction --no-dev

FROM python:3.9-slim

WORKDIR /app
COPY --from=builder /build/.venv /app/.venv
ENV PATH=/app/.venv/bin:$PATH
COPY pain001 /app/pain001

ENTRYPOINT ["python", "-m", "pain001"]
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import pain001; print('healthy')" || exit 1

FROM python:3.10

COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /bin/uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ ./src/

ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "src/pipeline_mapper.py"]

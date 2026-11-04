FROM python:3.10

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y build-essential graphviz libgraphviz-dev pkg-config libhdf5-dev && apt-get clean && rm \
    -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /bin/uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

RUN mkdir -p src/config src/curated_data src/dataset src/graph src/bitmaps

COPY src/csv_parser.py ./src
COPY src/bitmap_builder.py ./src
COPY src/pull_anndata.py ./src
COPY src/generate_rdf.py ./src
COPY src/process.py ./src

ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "src/process.py"]

FROM python:3.10

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y build-essential graphviz libgraphviz-dev pkg-config libhdf5-dev && apt-get clean && rm \
    -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

RUN mkdir -p src/config src/curated_data src/dataset src/graph

COPY src/csv_parser.py ./src
COPY src/pull_anndata.py ./src
COPY src/generate_rdf.py ./src
COPY src/process.py ./src

CMD ["python", "src/process.py"]

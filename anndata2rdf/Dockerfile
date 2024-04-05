FROM python:3.9

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y build-essential graphviz libgraphviz-dev pkg-config zip unzip tar ninja-build  \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV VENV="/opt/env"
ENV PATH="$VENV/bin:$PATH"

RUN python -m venv $VENV

RUN python3 -m venv $VENV

RUN pip3 install --upgrade pip wheel

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY src/ ./src

CMD ["python", "src/process.py"]

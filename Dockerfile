# Use an official Python runtime as a parent image with Python 3.9
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential tar curl zip unzip clang-tidy clang-format doxygen cmake graphviz libgraphviz-dev pkg-config libssl-dev zlib1g-dev libtbb-dev libspdlog-dev wget && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install required Python build tools
RUN pip install --upgrade pip setuptools wheel

WORKDIR /app

# Copy the necessary directories and files into the container
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY src/ ./

CMD ["python", "./process.py"]

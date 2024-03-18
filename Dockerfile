# Use an official Python runtime as a parent image with Python 3.9
FROM ubuntu:22.04
# FROM python:3.9
# FROM tiledb/tiledb:base

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    tar  \
    curl  \
    zip  \
    unzip  \
    clang-tidy  \
    clang-format  \
    doxygen  \
    cmake  \
    graphviz  \
    libgraphviz-dev  \
    pkg-config  \
    libssl-dev  \
    zlib1g-dev  \
    libtbb-dev  \
    libspdlog-dev  \
    libssl-dev \
    git \
    wget  \
    python3 \
    python3-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# # Upgrade pip and install required Python build tools
# RUN pip3 install --upgrade pip setuptools wheel

# WORKDIR /app

RUN cd /tmp \
    && wget https://github.com/Kitware/CMake/releases/download/v3.28.3/cmake-3.28.3-linux-x86_64.tar.gz \
    && tar -xzf cmake-3.28.3-linux-x86_64.tar.gz \
    && cp -R cmake-3.28.3-linux-x86_64/bin /usr/ \
    && cp -R cmake-3.28.3-linux-x86_64/doc /usr/ \
    && cp -R cmake-3.28.3-linux-x86_64/man /usr/ \
    && cp -R cmake-3.28.3-linux-x86_64/share /usr/

# # Optional components to enable (defaults to empty).
# ARG enable
# # Release version number of TileDB to install.
# ARG version=2.0.1
# # Release version number of TileDB-Py to install.
# # -- see below --

# RUN mkdir /home/tiledb

# # # Install TileDB
# # RUN wget -P /home/tiledb https://github.com/TileDB-Inc/TileDB/archive/${version}.tar.gz \
# #     && tar xzf /home/tiledb/${version}.tar.gz -C /home/tiledb \
# #     && rm /home/tiledb/${version}.tar.gz \
# #     && cd /home/tiledb/TileDB-${version} \
# #     && mkdir build \
# #     && cd build \
# #     && ../bootstrap --prefix=/usr/local --enable-azure --enable-s3 --enable-serialization --enable=${enable} \
# #     && make -j$(nproc) \
# #     && make -j$(nproc) examples \
# #     && make install-tiledb \
# #     && rm -rf /home/tiledb/TileDB-${version}

# # # Release version number of TileDB-Py to install.
# ARG pyversion=0.6.0
# ENV pyversion=$pyversion SETUPTOOLS_SCM_PRETEND_VERSION=$pyversion

# # # -----------------------------------------------------------------------------

# # Install Python bindings
# # RUN wget https://github.com/TileDB-Inc/TileDB-Py/archive/${pyversion}.tar.gz -O /home/tiledb/Py-${pyversion}.tar.gz \
# #     && tar xzf /home/tiledb/Py-${pyversion}.tar.gz -C /home/tiledb \
# #     && rm /home/tiledb/Py-${pyversion}.tar.gz \
# #     && cd /home/tiledb/TileDB-Py-${pyversion} \
# #     && pip3 install -r requirements.txt \
# #     # && python3 setup.py install --tiledb=/usr/local \
# #     && python3 setup.py install \
# #     && rm -rf /home/tiledb/TileDB-Py-${pyversion}

# # EXPOSE 22

# # this can be removed for TileDB-Py 0.4.3
# # ENV LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"

# RUN pip3 install tiledbsoma
RUN pip3 install git+https://github.com/single-cell-data/TileDB-SOMA.git@1.7.2#subdirectory=apis/python

# Copy the necessary directories and files into the container
COPY requirements.txt ./
RUN pip3 install -r requirements.txt

COPY src/ ./

CMD ["python", "./process.py"]

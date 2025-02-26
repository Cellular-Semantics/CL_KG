FROM python:3.10

SHELL ["/bin/bash", "-c"]

WORKDIR /app

COPY requirements.txt ./
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

COPY src/ ./src/

CMD ["python", "src/pipeline_mapper.py"]

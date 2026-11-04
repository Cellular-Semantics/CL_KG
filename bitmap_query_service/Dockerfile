FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

ENV PYTHONPATH=/app/src
ENV BITMAP_DIR=/app/bitmaps
ENV PORT=8000

CMD ["uvicorn", "bitmap_query_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

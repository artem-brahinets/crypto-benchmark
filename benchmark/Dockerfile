FROM python:3.14-slim

WORKDIR /app

COPY benchmark.py .
COPY config.py .

RUN pip install --no-cache-dir requests matplotlib

CMD ["python", "benchmark.py"]
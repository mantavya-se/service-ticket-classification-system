FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY rag/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements.txt

COPY rag/ ./rag/
COPY infrastructure/s3_storage.py ./infrastructure/s3_storage.py
COPY infrastructure/__init__.py ./infrastructure/__init__.py

CMD ["python3", "-m", "rag.init"]
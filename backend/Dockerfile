FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for compiling dependencies or FAISS if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port
EXPOSE 8000

# Command to run API server
CMD ["python", "main.py"]

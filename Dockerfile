FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git ffmpeg libgl1 libnetcdf-dev && \
    rm -rf /var/lib/apt/lists/*

COPY ./app /app/app
COPY ./requirements.txt /app/requirements.txt

# Upgrade pip and install deps
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

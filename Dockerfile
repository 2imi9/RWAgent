# Use an official Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Copy files
COPY ./app /app/app
COPY ./requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Expose the API port
EXPOSE 8080

# Start FastAPI app with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

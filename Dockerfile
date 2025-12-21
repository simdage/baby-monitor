# Stage 1: Build React App
FROM node:18-alpine as build
WORKDIR /app/frontend

# Copy package files
COPY frontend/package.json ./
# We don't have package-lock.json yet, so we just install
RUN npm install

# Copy source code
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Install additional dependencies for the API server
RUN pip install fastapi uvicorn google-cloud-bigquery python-dotenv

# Copy source code
COPY src/ ./src/
COPY cloud_function/ ./cloud_function/
# We might need .env if not passed via docker-compose, but usually we don't copy secrets in Dockerfile.
# Copy built frontend
COPY --from=build /app/frontend/dist ./frontend/dist

# Expose port
EXPOSE 8000

# Run the server
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]

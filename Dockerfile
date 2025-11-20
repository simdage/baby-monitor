FROM ubuntu:24.04

# Install system dependencies required for pyaudio and audio support
RUN apt-get update && apt-get install -y \
    python3-pyaudio \
    portaudio19-dev \
    python3-dev \
    gcc \
    g++ \
    alsa-utils \
    alsa-base \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY pyproject.toml uv.lock ./

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Install Python dependencies
RUN uv sync

# Copy application code
COPY . .

# Run the application
CMD ["uv", "run", "main.py"]

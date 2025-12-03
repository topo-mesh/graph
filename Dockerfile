# --- STAGE 1: BUILD ---
# Use a slim image for a smaller build size, but ensure necessary build tools are present.
FROM python:3.12-slim as builder

# Install system dependencies required for C-extensions like psutil,
# and for other libraries like pydantic, requests, etc.
# The 'build-essential' package is for Debian-based slim images.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    musl-dev \
    libffi-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy only the requirements file first to take advantage of Docker layer caching
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir helps reduce the image size
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# --- STAGE 2: FINAL (Runtime) ---
# Use a minimal, non-build image for the final container
FROM python:3.12-slim

# Set environment variables for non-buffered output
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 8000 # Default port for uvicorn/Railway/Render

# Set the working directory
WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy the application code
COPY main.py .
# Copy the .env file (you can secure this differently in production)
COPY .env .

# Expose the port (informative only, your hosting platform will handle the actual port mapping)
EXPOSE 8000

# Run the application using uvicorn's exec form for proper signal handling
# We explicitly use the variables defined in main.py to start the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
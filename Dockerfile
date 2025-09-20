# Use Python base image
FROM python:3.10-slim

# Set workdir
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Install supervisor to run multiple processes
RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*

# Add supervisor config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose Flask port
EXPOSE 1000

# Start supervisor (runs Flask + Bot together)
CMD ["/usr/bin/supervisord"]

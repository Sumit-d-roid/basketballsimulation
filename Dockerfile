# Use official Python runtime as base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install Node.js for frontend build
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt /app/backend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copy the rest of the application
COPY . /app

# Build frontend
WORKDIR /app/frontend
RUN npm install && npm run build

# Initialize database if needed
WORKDIR /app/backend
RUN if [ ! -f basketball_sim.db ]; then \
    python seed_data.py && \
    python add_free_agents.py; \
    fi

# Go back to app root
WORKDIR /app

# Make start script executable
RUN chmod +x start.sh

# Expose port (Railway will set PORT env variable)
EXPOSE 8080

# Start the application
CMD ["./start.sh"]

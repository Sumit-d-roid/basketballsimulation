# Use official Python runtime as base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install Node.js
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt backend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt gunicorn

# Copy entire project
COPY . .

# Build frontend
RUN cd frontend && npm install && npm run build

# Initialize database
RUN cd backend && python seed_data.py && python add_free_agents.py

# Set working directory to backend
WORKDIR /app/backend

# Expose port
EXPOSE 8080

# Set environment
ENV PYTHONUNBUFFERED=1

# Start gunicorn
CMD ["python3", "start_gunicorn.py"]

# Use a slim Python image for efficiency
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install system dependencies for PostgreSQL (psycopg) and healthy builds
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project code
COPY . /app/

# Expose the port Django runs on
EXPOSE 8000

# Start the server (using 0.0.0.0 to allow external Docker access)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
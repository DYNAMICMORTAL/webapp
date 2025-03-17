FROM python:3.9-slim

# Set work directory
WORKDIR /app

# Install system dependencies including pkg-config
RUN apt-get update && \
    apt-get install -y default-libmysqlclient-dev pkg-config gcc python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY webapp/bankapp/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY webapp/bankapp /app/

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "bankapp.wsgi:application"]
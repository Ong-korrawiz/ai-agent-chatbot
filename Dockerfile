# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install python-dotenv for .env file support
RUN pip install python-dotenv

# Copy source code
COPY src/ ./src/

# Expose port (adjust as needed)
EXPOSE 8000:8000

# Default command (adjust based on your main script)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
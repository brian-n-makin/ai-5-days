# Use an official lightweight Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy dependency definition and install
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . /app/

# Install the application package
RUN pip install -e .

# Expose any ports (none for CLI, but good practice if web gets added)
# EXPOSE 8000

# Set entry point
ENTRYPOINT ["tutor-agent"]

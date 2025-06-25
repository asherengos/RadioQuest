# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Check python version before anything
RUN python --version

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Using --verbose to get more output
RUN pip install --no-cache-dir --verbose -r requirements.txt

# Check for dependency conflicts
RUN pip check

# Check python version after install
RUN python --version

# Copy the rest of the application's code into the container at /app
COPY . .

# Run cache-busting script to append ?v=<timestamp> to static asset URLs in CSS
RUN python cache_buster.py

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable
ENV PORT 8080

# Use Gunicorn for production with verbose logging
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "0", "--log-level", "debug", "--log-file", "-", "app:app"]

# Use Python's built-in server for debugging to get raw logs
# CMD ["python", "app.py"] 
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container
COPY templater /app

COPY requirements.txt /app/

# Install dependencies
RUN pip install -r requirements.txt

# Expose the port the app runs on
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
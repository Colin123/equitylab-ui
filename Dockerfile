# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install any needed packages
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8050 available to the outside world (adjust if needed)
EXPOSE 80

# Run app.py with Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:80", "app:server"]

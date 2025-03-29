# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Create directory for SSL certificates
RUN mkdir -p /etc/ssl/certs/

# Add your Python and app setup commands (as before)
# Copy your project code and install dependencies:
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# Expose HTTPS port 8050
EXPOSE 8050

# Start Gunicorn to serve the app
CMD ["gunicorn", "-b", "0.0.0.0:8050", "--certfile=/etc/ssl/certs/fullchain.pem", "--keyfile=/etc/ssl/certs/privkey.pem", "app:server"]

# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Create a directory for SSL certificates inside the container
# RUN mkdir -p /etc/ssl/certs/

# Copy your project files and install dependencies
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# Expose HTTPS port (8050 in this example)
# EXPOSE 443
EXPOSE 8050

# Start the app using Gunicorn with your SSL certificate and key
# CMD ["gunicorn", "-b", "0.0.0.0:443", "--certfile=/etc/ssl/certs/recursa_biz.cert", "--keyfile=/etc/ssl/certs/recursa_biz.key", "app:server"]
# CMD ["gunicorn", "-b", "0.0.0.0:443", "app:server"]

# CMD ["gunicorn", "-b", "0.0.0.0:8050", "--access-logfile=-", "app:server"]
# CMD ["gunicorn", "-b", "0.0.0.0:8050", "--access-logfile=-", "Auth0Test:app"]
CMD ["gunicorn", "-b", "0.0.0.0:8050", "--access-logfile=-", "RRGCharts:app"]

RUN apt-get update && apt-get install -y curl

# HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
# CMD curl -f http://0.0.0.0:8050/health || exit 1

# FIXME Force true for now, can't access health since auth0 needs a login
HEALTHCHECK CMD exit 0




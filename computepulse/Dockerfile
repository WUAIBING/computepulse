# Use a lightweight Python image
FROM python:3.9-slim

# Install Node.js (for building frontend)
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY package*.json ./
RUN npm install

# Copy project files
COPY . .

# Build frontend
RUN npm run build

# Expose the server port
EXPOSE 3001

# Run the startup script
# We need a shell script to run both background fetcher and server
COPY scripts/start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]

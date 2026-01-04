# Base Image
FROM python:3.9-slim

# 1. Install Basic Tools
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Google Chrome (Direct Download Method)
# This bypasses the "apt-key" error by downloading the file directly
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

# 3. Set Working Directory
WORKDIR /app

# 4. Copy Files (Note: We removed .env because Render uses Secrets instead)
COPY requirements.txt .
COPY proxyscrape_premium_http_proxies.txt .
COPY app.py .

# 5. Install Python Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6. Expose Port
EXPOSE 8501

# 7. Run the App
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
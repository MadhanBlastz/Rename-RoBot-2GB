FROM python:3.11-slim

# Install ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set up your application
COPY . /app
WORKDIR /app

# Install Python dependencies
RUN pip install -r requirements.txt

CMD ["python", "bot.py"]

FROM jrottenberg/ffmpeg:4.3-alpine

# Install Python
RUN apk add --no-cache python3 py3-pip

# Copy your application code
COPY . /app
WORKDIR /app

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Run the bot
CMD ["python3", "bot.py"]

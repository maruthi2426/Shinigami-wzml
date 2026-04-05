FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN apt update && apt install -y \
    aria2 \
    qbittorrent-nox \
    ffmpeg \
    curl \
    && ln -s /usr/bin/qbittorrent-nox /usr/bin/stormtorrent \
    && mkdir -p sabnzbd \
    && pip install --no-cache-dir -r requirements.txt

# 🔥 START ARIA2 + BOT
CMD aria2c \
    --enable-rpc \
    --rpc-listen-all=true \
    --rpc-allow-origin-all \
    --rpc-listen-port=6800 \
    --daemon=true \
    && python3 -m bot

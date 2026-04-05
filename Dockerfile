FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN apt update && apt install -y \
    aria2 \
    qbittorrent-nox \
    ffmpeg \
    && ln -s /usr/bin/qbittorrent-nox /usr/bin/stormtorrent \
    && mkdir -p sabnzbd \
    && pip install --no-cache-dir -r requirements.txt

CMD ["python3", "-m", "bot"]

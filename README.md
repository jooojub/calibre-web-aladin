# Dockerfile
```
FROM lscr.io/linuxserver/calibre-web:latest
COPY ./aladin.py /app/calibre-web/cps/metadata_provider/
```
# Build
docker build -t jooojub-calibre-web .

# Create docker compose

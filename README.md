# Immich Frame Light

Digital photo frame for Immich, optimized for legacy devices like iPad Mini 1 running iOS 9.3.5.

## Features

- Pure vanilla JS (ES5 compatible) - no frameworks, no dependencies on frontend
- Black background, centered images with `object-fit: contain`
- Image preloading to prevent flicker
- Error handling for failed loads
- Configurable slideshow interval
- Docker support with minimal image size

## Quick Start (Docker)

```bash
docker build -t immichframe-light .
docker run -d \
  -p 5000:5000 \
  -e IMMICH_URL=http://192.168.1.50:2283 \
  -e IMMICH_API_KEY=your_api_key_here \
  -e IMMICH_ALBUM_ID=your_album_uuid_here \
  -e INTERVAL_SECONDS=15 \
  --name immichframe \
  --restart unless-stopped \
  immichframe-light
```

## Docker Compose

```yaml
version: "3.8"
services:
  immichframe:
    build: .
    ports:
      - "5000:5000"
    environment:
      - IMMICH_URL=http://192.168.1.50:2283
      - IMMICH_API_KEY=your_api_key_here
      - IMMICH_ALBUM_ID=your_album_uuid_here
      - INTERVAL_SECONDS=15
    restart: unless-stopped
```

## Portainer Setup

1. Go to **Stacks** > **Add stack**
2. Choose **Web editor** and paste the content of `docker-compose.yml`
3. Fill in the environment variables under **Environment variables**:
   - `IMMICH_URL` - Your Immich server URL
   - `IMMICH_API_KEY` - Your API key
   - `IMMICH_ALBUM_ID` - Album UUID
   - `INTERVAL_SECONDS` - Slideshow interval (optional, default: 15)
4. Deploy the stack

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `IMMICH_URL` | Base URL of your Immich server | `http://localhost:2283` |
| `IMMICH_API_KEY` | API key from Immich user settings | (required) |
| `IMMICH_ALBUM_ID` | UUID of the target album | (required) |
| `INTERVAL_SECONDS` | Time between photo changes | `15` |

### Finding your Album UUID

1. Open Immich web UI
2. Navigate to the album you want
3. The URL will look like: `http://your-server:2283/albums/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
4. Copy the UUID from the URL

## Development

```bash
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000` in your browser.

## Compatibility

Tested and optimized for:
- iOS 9.3.5 (Safari / Dolphin Browser)
- iPad Mini 1 (A5 chip)
- Modern browsers (Chrome, Firefox, Safari, Edge)

## License

MIT

# Immich Frame Light

Digital photo frame for Immich, optimized for legacy devices like iPad Mini 1 running iOS 9.3.5.

## Features

- **ES5 Compatible** - Pure vanilla JavaScript, works on iOS 9.3.5 Safari/Dolphin
- **Multiple Albums** - Combine assets from several albums using comma-separated IDs
- **Memories** - Highlight photos taken on this day in previous years
- **Weather Display** - Current weather with temperature, description and extended info (OpenWeatherMap)
- **Photo Info** - Album name, people, location, date with SVG icons and portrait splitting
- **Image Resizing** - Server-side thumbnail resizing/compression with Pillow and LRU caching
- **Server Time Sync** - Accurate clock synchronized with server
- **Responsive Design** - Works on tablets, phones, and desktop
- **Docker Support** - Minimal image served by Gunicorn, easy deployment

## Quick Start (Docker)

```bash
docker build -t immichframe-light .
docker run -d \
  -p 5000:5000 \
  -e IMMICH_URL=http://192.168.1.50:2283 \
  -e IMMICH_API_KEY=your_api_key_here \
  -e IMMICH_ALBUM_ID=your_album_uuid_here \
  --name immichframe \
  --restart unless-stopped \
  immichframe-light
```

To use more than one album, separate the IDs with commas:

```bash
  -e IMMICH_ALBUM_ID=album_id_1,album_id_2,album_id_3 \
```

## Docker Compose

```yaml
version: "3.8"
services:
  immichframe:
    image: ghcr.io/fernandodimas/immichframe_light:latest
    container_name: immichframe
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      # Immich connection
      - IMMICH_URL=http://192.168.1.50:2283
      - IMMICH_API_KEY=your_api_key_here
      - IMMICH_ALBUM_ID=your_album_uuid_here     # or "id1,id2,id3"

      # Slideshow settings
      - INTERVAL_SECONDS=20
      - TRANSITION_DURATION=2
      - SHUFFLE=true

      # Display settings
      - SHOW_CLOCK=true
      - CLOCK_FORMAT=HH:mm
      - CLOCK_DATE_FORMAT=eeee, d 'de' MMMM 'de' yyyy
      - SHOW_PROGRESS_BAR=true
      - SHOW_PHOTO_DATE=true
      - PHOTO_DATE_FORMAT=dd/MM/yyyy
      - SHOW_IMAGE_DESC=true
      - SHOW_PEOPLE_DESC=true
      - SHOW_ALBUM_NAME=true
      - SHOW_IMAGE_LOCATION=true
      - LANGUAGE=pt

      # Memories / layout
      - SHOW_MEMORIES=true
      - PRIORITIZE_MEMORIES=true
      - SPLIT_PORTRAIT=true

      # Image effect settings
      - IMAGE_ZOOM=true
      - IMAGE_PAN=false
      - IMAGE_FILL=false

      # Style settings
      - PRIMARY_COLOR=#f5deb3
      - SECONDARY_COLOR=#000000
      - STYLE=none
      - BASE_FONT_SIZE=17px
      - IMAGE_LOCATION_FORMAT=City,State,Country

      # Image resizing / cache
      - RESIZE_IMAGES=true
      - MAX_IMAGE_WIDTH=1024
      - MAX_IMAGE_HEIGHT=768
      - IMAGE_QUALITY=82
      - THUMB_CACHE_SIZE=50

      # Weather settings
      - WEATHER_API_KEY=your_openweather_api_key
      - UNIT_SYSTEM=metric
      - WEATHER_LAT_LONG=40.730610,-73.935242
      - SHOW_WEATHER_DESCRIPTION=true
      - SHOW_WEATHER_EXTENDED=true

      # Night mode / brightness
      - NIGHT_MODE=false
      - NIGHT_MODE_START=22:00
      - NIGHT_MODE_END=07:00
      - BRIGHTNESS=100
      - NIGHT_MODE_BRIGHTNESS=0

      # Timezone
      - TIMEZONE=-3
```

## Portainer Setup

1. Go to **Stacks** > **Add stack**
2. Choose **Web editor** and paste the content of `docker-compose.yml`
3. Fill in the environment variables under **Environment variables** (see below)
4. Deploy the stack

## Environment Variables

### Required

| Variable | Description | Default |
|----------|-------------|---------|
| `IMMICH_URL` | Base URL of your Immich server | `http://localhost:2283` |
| `IMMICH_API_KEY` | API key from Immich user settings | (required) |
| `IMMICH_ALBUM_ID` | One or more album UUIDs, separated by commas (e.g. `id1,id2`) | (required) |

### Slideshow Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `INTERVAL_SECONDS` | Time between photo changes | `20` |
| `TRANSITION_DURATION` | Duration of fade transition (seconds) | `2` |
| `SHUFFLE` | Randomize photo order | `true` |

### Display Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `SHOW_CLOCK` | Display current time | `true` |
| `CLOCK_FORMAT` | Time format (HH:mm, hh:mm a) | `HH:mm` |
| `CLOCK_DATE_FORMAT` | Date format for clock | `eeee, d 'de' MMMM 'de' yyyy` |
| `SHOW_PROGRESS_BAR` | Display progress bar | `true` |
| `SHOW_PHOTO_DATE` | Display photo date | `true` |
| `PHOTO_DATE_FORMAT` | Date format for photos (`dd`, `d`, `MM`, `MMMM`, `yyyy`, `eeee`) | `dd/MM/yyyy` |
| `SHOW_IMAGE_DESC` | Display image description | `true` |
| `SHOW_PEOPLE_DESC` | Display people names | `true` |
| `SHOW_ALBUM_NAME` | Display album name | `true` |
| `SHOW_IMAGE_LOCATION` | Display photo location | `true` |
| `LANGUAGE` | Language for dates and UI (`pt`, `en`, `es`, `fr`, `de`) | `pt` |
| `BRIGHTNESS` | Software brightness level (10-100). Can also be changed from the settings menu | `100` |

### Memories / Layout

| Variable | Description | Default |
|----------|-------------|---------|
| `SHOW_MEMORIES` | Show photos taken on this day in previous years | `true` |
| `PRIORITIZE_MEMORIES` | Sort memories to the top of the slideshow | `true` |
| `SPLIT_PORTRAIT` | Split portrait photos into two panels | `true` |

### Image Effects

| Variable | Description | Default |
|----------|-------------|---------|
| `IMAGE_ZOOM` | Ken Burns zoom effect | `true` |
| `IMAGE_PAN` | Pan animation in random direction | `false` |
| `IMAGE_FILL` | Fill available space (may crop) | `false` |

### Style Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `PRIMARY_COLOR` | Primary UI color (hex) | `#f5deb3` |
| `SECONDARY_COLOR` | Secondary UI color (hex) | `#000000` |
| `STYLE` | Background style | `none` |
| `BASE_FONT_SIZE` | Base font size | `17px` |
| `IMAGE_LOCATION_FORMAT` | Location format | `City,State,Country` |

### Image Resizing / Cache

| Variable | Description | Default |
|----------|-------------|---------|
| `RESIZE_IMAGES` | Resize and compress thumbnails with Pillow before serving | `true` |
| `MAX_IMAGE_WIDTH` | Maximum processed thumbnail width in pixels | `1024` |
| `MAX_IMAGE_HEIGHT` | Maximum processed thumbnail height in pixels | `768` |
| `IMAGE_QUALITY` | JPEG quality for processed thumbnails (1-100) | `82` |
| `THUMB_CACHE_SIZE` | Number of processed thumbnails held in the in-memory LRU cache | `50` |

> When `RESIZE_IMAGES=false` (or Pillow is unavailable), thumbnails are proxied from Immich without modification. Processed images are served with `Cache-Control: public, max-age=86400`.

### Weather Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `WEATHER_API_KEY` | OpenWeatherMap API key | (disabled) |
| `UNIT_SYSTEM` | Temperature unit | `metric` |
| `WEATHER_LAT_LONG` | Weather location (lat,lon) | `40.730610,-73.935242` |
| `SHOW_WEATHER_DESCRIPTION` | Display weather description | `true` |
| `SHOW_WEATHER_EXTENDED` | Display min/max and feels-like temperatures | `true` |

> Weather responses are cached in memory for 15 minutes. The frontend uses native SVG icons; the legacy `/api/weather-icon/<code>` route is kept for compatibility and returns 404 when no cached PNG exists.

### Night Mode

| Variable | Description | Default |
|----------|-------------|---------|
| `NIGHT_MODE` | Enable night mode (black screen) | `false` |
| `NIGHT_MODE_START` | Start time (HH:mm) | `22:00` |
| `NIGHT_MODE_END` | End time (HH:mm) | `07:00` |
| `NIGHT_MODE_BRIGHTNESS` | Night-mode brightness (0-100). `0` keeps the original black screen + paused slideshow; `1-100` keeps the slideshow running with a software dimmer | `0` |

- `BRIGHTNESS` sets the software dimmer used outside night mode. The frame's screen backlight is not changed — a black overlay reduces perceived brightness. Use the **Brilho** `-` / `+` buttons in the settings menu to adjust it on the device; manual changes are saved in the browser and survive reloads.
- With `NIGHT_MODE_BRIGHTNESS=0`, night mode behaves as before: full black screen, slideshow and progress bar paused. With a value above `0`, the night overlay is disabled and the slideshow keeps running at that brightness.

### Timezone

| Variable | Description | Default |
|----------|-------------|---------|
| `TIMEZONE` | UTC offset in hours, ISO offset or named timezone | (system default) |

Examples:
- `-3` for Brasilia (UTC-3)
- `-5` for New York (UTC-5)
- `1` for London (UTC+1)
- `America/Sao_Paulo` (named timezone)

## Finding your Album UUID

1. Open Immich web UI
2. Navigate to the album you want
3. The URL will look like: `http://your-server:2283/albums/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
4. Copy the UUID from the URL
5. To combine albums, list their UUIDs separated by commas in `IMMICH_ALBUM_ID`

## Getting an Immich API Key

1. Open Immich web UI
2. Go to **User Settings** > **API Keys**
3. Click **New API Key**
4. Copy the generated key

## Getting a Weather API Key

1. Go to [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for a free account
3. Go to **My API Keys**
4. Copy your API key

## Navigation

- **Left/Right arrows** - Navigate between photos (appear on hover/touch)
- **Progress bar** - Shows time until next photo
- **Photo info** - Displays album, people, location, and date

## Development

```bash
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000` in your browser.

In production the container runs the app with Gunicorn (`app:app`, 1 worker / 4 threads, 60s timeout).

## Compatibility

Tested and optimized for:
- iOS 9.3.5 (Safari / Dolphin Browser)
- iPad Mini 1 (A5 chip)
- Modern browsers (Chrome, Firefox, Safari, Edge)

## License

MIT

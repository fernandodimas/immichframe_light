# Immich Frame Light

Digital photo frame for Immich, optimized for legacy devices like iPad Mini 1 running iOS 9.3.5.

## Features

- **ES5 Compatible** - Pure vanilla JavaScript, works on iOS 9.3.5 Safari/Dolphin
- **Weather Display** - Current weather with temperature and description (OpenWeatherMap)
- **Photo Info** - Album name, people, location, and date with SVG icons
- **Image Effects** - Ken Burns zoom, pan animations, and fill mode
- **Server Time Sync** - Accurate clock synchronized with server
- **Responsive Design** - Works on tablets, phones, and desktop
- **Docker Support** - Minimal image size, easy deployment

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
      - IMMICH_ALBUM_ID=your_album_uuid_here

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

      # Weather settings
      - WEATHER_API_KEY=your_openweather_api_key
      - UNIT_SYSTEM=metric
      - WEATHER_LAT_LONG=40.730610,-73.935242
      - SHOW_WEATHER_DESCRIPTION=true
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
| `IMMICH_ALBUM_ID` | UUID of the target album | (required) |

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
| `PHOTO_DATE_FORMAT` | Date format for photos | `dd/MM/yyyy` |
| `SHOW_IMAGE_DESC` | Display image description | `true` |
| `SHOW_PEOPLE_DESC` | Display people names | `true` |
| `SHOW_ALBUM_NAME` | Display album name | `true` |
| `SHOW_IMAGE_LOCATION` | Display photo location | `true` |
| `LANGUAGE` | Language for weather and UI | `pt` |

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

### Weather Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `WEATHER_API_KEY` | OpenWeatherMap API key | (disabled) |
| `UNIT_SYSTEM` | Temperature unit | `metric` |
| `WEATHER_LAT_LONG` | Weather location (lat,lon) | `40.730610,-73.935242` |
| `SHOW_WEATHER_DESCRIPTION` | Display weather description | `true` |

## Finding your Album UUID

1. Open Immich web UI
2. Navigate to the album you want
3. The URL will look like: `http://your-server:2283/albums/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
4. Copy the UUID from the URL

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

## Compatibility

Tested and optimized for:
- iOS 9.3.5 (Safari / Dolphin Browser)
- iPad Mini 1 (A5 chip)
- Modern browsers (Chrome, Firefox, Safari, Edge)

## License

MIT

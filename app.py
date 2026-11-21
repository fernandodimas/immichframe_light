"""
Immich Frame - Digital Photo Frame for Legacy Devices
=====================================================
A minimalist Flask app designed to run slideshow from an Immich album,
optimized for iOS 9.3.5 Safari and other legacy browsers.
"""

import os
import re
import logging
import time
import threading
from collections import OrderedDict
from datetime import datetime, timezone, timedelta
from io import BytesIO

import requests
from flask import Flask, render_template, jsonify, Response

try:
    from PIL import Image, ImageOps
    PIL_AVAILABLE = True
except ImportError:  # Pillow is optional: without it thumbnails are proxied as-is
    Image = None
    ImageOps = None
    PIL_AVAILABLE = False

app = Flask(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Shared HTTP session: keeps connections alive with both Immich and OpenWeatherMap.
_http_session = requests.Session()

WEATHER_ICONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_icons")
os.makedirs(WEATHER_ICONS_DIR, exist_ok=True)

# Immich connection
IMMICH_URL = os.environ.get("IMMICH_URL", "http://localhost:2283").rstrip("/")
IMMICH_API_KEY = os.environ.get("IMMICH_API_KEY", "")
IMMICH_ALBUM_ID = os.environ.get("IMMICH_ALBUM_ID", "")

# Slideshow settings
INTERVAL_SECONDS = int(os.environ.get("INTERVAL_SECONDS", "15"))
TRANSITION_DURATION = float(os.environ.get("TRANSITION_DURATION", "2"))
SHUFFLE = os.environ.get("SHUFFLE", "true").lower() in ("true", "1", "yes")

# Display settings
SHOW_CLOCK = os.environ.get("SHOW_CLOCK", "true").lower() in ("true", "1", "yes")
CLOCK_FORMAT = os.environ.get("CLOCK_FORMAT", "HH:mm")
CLOCK_DATE_FORMAT = os.environ.get("CLOCK_DATE_FORMAT", "eeee, d 'de' MMMM 'de' yyyy")
SHOW_PROGRESS_BAR = os.environ.get("SHOW_PROGRESS_BAR", "true").lower() in ("true", "1", "yes")
SHOW_PHOTO_DATE = os.environ.get("SHOW_PHOTO_DATE", "true").lower() in ("true", "1", "yes")
PHOTO_DATE_FORMAT = os.environ.get("PHOTO_DATE_FORMAT", "dd/MM/yyyy")
SHOW_IMAGE_DESC = os.environ.get("SHOW_IMAGE_DESC", "true").lower() in ("true", "1", "yes")
SHOW_PEOPLE_DESC = os.environ.get("SHOW_PEOPLE_DESC", "true").lower() in ("true", "1", "yes")
SHOW_ALBUM_NAME = os.environ.get("SHOW_ALBUM_NAME", "true").lower() in ("true", "1", "yes")
SHOW_IMAGE_LOCATION = os.environ.get("SHOW_IMAGE_LOCATION", "true").lower() in ("true", "1", "yes")
LANGUAGE = os.environ.get("LANGUAGE", "pt")

# Memory / layout settings
SHOW_MEMORIES = os.environ.get("SHOW_MEMORIES", "true").lower() in ("true", "1", "yes")
PRIORITIZE_MEMORIES = os.environ.get("PRIORITIZE_MEMORIES", "true").lower() in ("true", "1", "yes")
SPLIT_PORTRAIT = os.environ.get("SPLIT_PORTRAIT", "true").lower() in ("true", "1", "yes")

# Style settings
PRIMARY_COLOR = os.environ.get("PRIMARY_COLOR", "#f5deb3")
SECONDARY_COLOR = os.environ.get("SECONDARY_COLOR", "#000000")
STYLE = os.environ.get("STYLE", "none")
BASE_FONT_SIZE = os.environ.get("BASE_FONT_SIZE", "17px")
IMAGE_LOCATION_FORMAT = os.environ.get("IMAGE_LOCATION_FORMAT", "City,State,Country")

# Thumbnail resize settings
SHOW_WEATHER_EXTENDED = os.environ.get("SHOW_WEATHER_EXTENDED", "true").lower() in ("true", "1", "yes")
RESIZE_IMAGES = os.environ.get("RESIZE_IMAGES", "true").lower() in ("true", "1", "yes")
MAX_IMAGE_WIDTH = int(os.environ.get("MAX_IMAGE_WIDTH", "1024"))
MAX_IMAGE_HEIGHT = int(os.environ.get("MAX_IMAGE_HEIGHT", "768"))
IMAGE_QUALITY = int(os.environ.get("IMAGE_QUALITY", "82"))
THUMB_CACHE_SIZE = int(os.environ.get("THUMB_CACHE_SIZE", "50"))

# Weather settings
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "")
UNIT_SYSTEM = os.environ.get("UNIT_SYSTEM", "metric")
WEATHER_LAT_LONG = os.environ.get("WEATHER_LAT_LONG", "40.730610,-73.935242")
SHOW_WEATHER_DESCRIPTION = os.environ.get("SHOW_WEATHER_DESCRIPTION", "true").lower() in ("true", "1", "yes")
WEATHER_ICON_URL = os.environ.get("WEATHER_ICON_URL", "https://openweathermap.org/img/wn/{IconId}.png")
WEATHER_CACHE_TTL = 900  # 15 minutes

# Night mode settings
NIGHT_MODE = os.environ.get("NIGHT_MODE", "false").lower() in ("true", "1", "yes")
NIGHT_MODE_START = os.environ.get("NIGHT_MODE_START", "22:00")
NIGHT_MODE_END = os.environ.get("NIGHT_MODE_END", "07:00")

# Timezone settings (e.g., -3 for Brasilia, UTC-3, America/Sao_Paulo)
TIMEZONE = os.environ.get("TIMEZONE", "")

# In-memory caches
_assets_cache = {}
_assets_cache_time = 0
ASSETS_CACHE_TTL = 300  # 5 minutes

_thumb_cache = OrderedDict()
_thumb_cache_lock = threading.Lock()

_weather_cache = {}
_weather_cache_time = 0
_weather_cache_lock = threading.Lock()

# Date formatting vocabulary
_MONTHS = {
    "pt": ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
           "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"],
    "en": ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio",
           "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin",
           "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni",
           "Juli", "August", "September", "Oktober", "November", "Dezember"],
}

_WEEKDAYS = {
    "pt": ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
           "sexta-feira", "sábado", "domingo"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "es": ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"],
    "fr": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
    "de": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
}

_DATE_TOKEN_RE = re.compile(r"yyyy|MMMM|eeee|MM|dd|d")


def get_configured_timezone():
    """Return configured tzinfo or local timezone."""
    tz_str = (TIMEZONE or "").strip()
    if not tz_str:
        return datetime.now().astimezone().tzinfo

    upper_tz = tz_str.upper()
    if upper_tz.startswith("UTC") or upper_tz.startswith("GMT"):
        tz_str = tz_str[3:].strip()

    # Try numeric like -3, +3, -3.5, 3
    try:
        hours = float(tz_str)
        return timezone(timedelta(hours=hours))
    except ValueError:
        pass

    # Try ISO offset like -03:00 or +05:30
    if ":" in tz_str and (tz_str.startswith("-") or tz_str.startswith("+")):
        parts = tz_str.split(":")
        try:
            sign = -1 if parts[0].startswith("-") else 1
            h = abs(int(parts[0]))
            m = int(parts[1])
            return timezone(sign * timedelta(hours=h, minutes=m))
        except ValueError:
            pass

    # Try named timezone like "America/Sao_Paulo"
    try:
        import zoneinfo
        return zoneinfo.ZoneInfo(tz_str)
    except Exception as exc:
        logger.warning("Could not parse timezone '%s': %s. Falling back to server timezone.", tz_str, exc)
        return datetime.now().astimezone().tzinfo


def get_album_ids():
    """Return the list of album IDs configured in IMMICH_ALBUM_ID (comma separated)."""
    return [album_id.strip() for album_id in IMMICH_ALBUM_ID.split(",") if album_id.strip()]


def parse_photo_datetime(value):
    """Best-effort parse of an Immich date string into a datetime object."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value

    text = str(value).strip()
    if not text:
        return None

    formats = [
        "%Y:%m:%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def format_photo_date(value, fmt=None, lang=None):
    """Format a photo date using tokens: dd, d, MM, MMMM, yyyy, eeee."""
    dt = parse_photo_datetime(value)
    if dt is None:
        return ""

    fmt = fmt or PHOTO_DATE_FORMAT
    lang = (lang or LANGUAGE or "en").lower()
    if lang not in _MONTHS:
        lang = "en"

    months = _MONTHS[lang]
    weekdays = _WEEKDAYS[lang]

    def replace(match):
        token = match.group(0)
        if token == "yyyy":
            return "{:04d}".format(dt.year)
        if token == "MMMM":
            return months[dt.month - 1]
        if token == "eeee":
            return weekdays[dt.weekday()]
        if token == "MM":
            return "{:02d}".format(dt.month)
        if token == "dd":
            return "{:02d}".format(dt.day)
        if token == "d":
            return str(dt.day)
        return token

    # Only replace tokens outside single-quoted literals, so formats such as
    # "eeee, d 'de' MMMM 'de' yyyy" keep the literal "de" intact.
    chunks = fmt.split("'")
    formatted = "".join(
        chunk if index % 2 else _DATE_TOKEN_RE.sub(replace, chunk)
        for index, chunk in enumerate(chunks)
    )
    return formatted


def build_location(exif):
    """Build the location string from EXIF data respecting IMAGE_LOCATION_FORMAT."""
    exif = exif or {}
    city = (exif.get("city") or "").strip()
    state = (exif.get("state") or "").strip()
    country = (exif.get("country") or "").strip()

    parts = []
    if "City" in IMAGE_LOCATION_FORMAT and city:
        parts.append(city)
    if "State" in IMAGE_LOCATION_FORMAT and state:
        parts.append(state)
    if "Country" in IMAGE_LOCATION_FORMAT and country:
        parts.append(country)
    return ", ".join(parts)


def compute_is_portrait(exif):
    """Return True/False for portrait orientation, or None when unknown."""
    exif = exif or {}
    try:
        width = int(exif.get("exifImageWidth") or 0)
        height = int(exif.get("exifImageHeight") or 0)
    except (TypeError, ValueError):
        return None

    if not width or not height:
        return None

    orientation = str(exif.get("orientation", ""))
    if orientation in ("5", "6", "7", "8"):
        width, height = height, width

    return height > width


def compute_memory(date_value, today):
    """Return (isMemory, yearsAgo) for a photo compared to today's date."""
    dt = parse_photo_datetime(date_value)
    if dt is None:
        return False, 0

    if dt.year < today.year and dt.month == today.month and dt.day == today.day:
        return True, today.year - dt.year
    return False, 0


logger.info("IMMICH_URL: %s", IMMICH_URL)
logger.info("IMMICH_ALBUM_ID: %s", IMMICH_ALBUM_ID or "NOT SET")
logger.info("INTERVAL: %ds, TRANSITION: %.1fs, SHUFFLE: %s", INTERVAL_SECONDS, TRANSITION_DURATION, SHUFFLE)
logger.info("RESIZE_IMAGES: %s, Pillow available: %s", RESIZE_IMAGES, PIL_AVAILABLE)


def fetch_album_assets():
    """Fetch assets from one or more Immich albums and return normalized asset data."""
    global _assets_cache, _assets_cache_time

    album_ids = get_album_ids()
    cache_key = ",".join(album_ids)
    if cache_key in _assets_cache and (time.time() - _assets_cache_time) < ASSETS_CACHE_TTL:
        logger.debug("Returning cached assets for albums %s", cache_key)
        return _assets_cache[cache_key]

    if not IMMICH_API_KEY or not album_ids:
        logger.warning("IMMICH_API_KEY or IMMICH_ALBUM_ID not configured")
        return []

    headers = {"x-api-key": IMMICH_API_KEY}
    search_url = "{}/api/search/metadata".format(IMMICH_URL)
    today = datetime.now(timezone.utc).astimezone(get_configured_timezone())

    seen_ids = set()
    result = []

    for album_id in album_ids:
        album_assets = []
        album_name = ""

        # 1) Preferred: GET the album itself (returns albumName + full asset details).
        album_url = "{}/api/albums/{}".format(IMMICH_URL, album_id)
        try:
            resp = _http_session.get(album_url, headers=headers, timeout=30)
            logger.debug("GET %s -> %d", album_url, resp.status_code)
            if resp.status_code == 200:
                data = resp.json()
                album_name = data.get("albumName", "") or ""
                album_assets = data.get("assets", []) or []
        except requests.RequestException as exc:
            logger.warning("Could not GET album %s: %s", album_id, exc)
        except ValueError:
            logger.warning("Invalid JSON from album %s", album_id)

        # 2) Fallback: POST search/metadata when the album GET failed or had no assets.
        if not album_assets:
            try:
                payload = {"albumIds": [album_id], "size": 1000}
                resp = _http_session.post(search_url, json=payload, headers=headers, timeout=30)
                logger.debug("POST %s -> %d", search_url, resp.status_code)
                if resp.status_code == 200:
                    data = resp.json()
                    album_assets = data.get("assets", {}).get("items", []) or []
                else:
                    logger.error("Immich search returned HTTP %d: %s", resp.status_code, resp.text[:300])
            except requests.RequestException as exc:
                logger.error("Failed to search album %s: %s", album_id, exc)
            except ValueError:
                logger.error("Invalid JSON from Immich search for album %s", album_id)

            # Best-effort album name if the first GET did not provide one.
            if not album_name:
                try:
                    resp = _http_session.get(album_url, headers=headers, timeout=15)
                    if resp.status_code == 200:
                        album_name = resp.json().get("albumName", "") or ""
                except Exception:
                    pass

        logger.debug("Album %s: %d assets", album_id, len(album_assets))

        # 3) Normalize, deduplicate and filter to images only.
        for asset in album_assets:
            asset_id = asset.get("id")
            if not asset_id or asset_id in seen_ids:
                continue
            if asset.get("type") == "VIDEO":
                continue

            seen_ids.add(asset_id)
            exif = asset.get("exifInfo", {}) or {}
            date_value = (asset.get("localDateTime")
                          or asset.get("fileCreatedAt")
                          or asset.get("createdAt")
                          or "")
            is_memory, years_ago = compute_memory(date_value, today)

            item = {
                "id": asset_id,
                "date": date_value,
                "formattedDate": format_photo_date(date_value),
                "description": asset.get("description") or exif.get("description") or "",
                "people": [p.get("name", "").strip() for p in (asset.get("people") or [])
                           if p.get("name", "").strip()],
                "location": build_location(exif),
                "albumName": album_name,
                "isPortrait": compute_is_portrait(exif),
                "isMemory": is_memory,
                "yearsAgo": years_ago,
            }
            result.append(item)

    # Memories first (stable sort keeps the original order inside each group).
    if PRIORITIZE_MEMORIES:
        result.sort(key=lambda item: not item["isMemory"])

    _assets_cache[cache_key] = result
    _assets_cache_time = time.time()

    logger.info("Loaded %d image assets from %d album(s)", len(result), len(album_ids))
    return result


@app.route("/")
def index():
    """Serve the main slideshow page."""
    return render_template(
        "index.html",
        primary_color=PRIMARY_COLOR,
        secondary_color=SECONDARY_COLOR,
        base_font_size=BASE_FONT_SIZE,
    )


@app.route("/api/slideshow")
def api_slideshow():
    """API endpoint to get slideshow data for JavaScript."""
    assets = fetch_album_assets()
    config = {
        "interval": INTERVAL_SECONDS,
        "transition": TRANSITION_DURATION,
        "shuffle": SHUFFLE,
        "showClock": SHOW_CLOCK,
        "clockFormat": CLOCK_FORMAT,
        "clockDateFormat": CLOCK_DATE_FORMAT,
        "showProgressBar": SHOW_PROGRESS_BAR,
        "showPhotoDate": SHOW_PHOTO_DATE,
        "photoDateFormat": PHOTO_DATE_FORMAT,
        "showImageDesc": SHOW_IMAGE_DESC,
        "showPeopleDesc": SHOW_PEOPLE_DESC,
        "showAlbumName": SHOW_ALBUM_NAME,
        "showImageLocation": SHOW_IMAGE_LOCATION,
        "primaryColor": PRIMARY_COLOR,
        "secondaryColor": SECONDARY_COLOR,
        "style": STYLE,
        "baseFontSize": BASE_FONT_SIZE,
        "language": LANGUAGE,
        "nightMode": NIGHT_MODE,
        "nightModeStart": NIGHT_MODE_START,
        "nightModeEnd": NIGHT_MODE_END,
        "timezone": TIMEZONE,
        "showWeatherDescription": SHOW_WEATHER_DESCRIPTION,
        "showWeatherExtended": SHOW_WEATHER_EXTENDED,
        "showMemories": SHOW_MEMORIES,
        "prioritizeMemories": PRIORITIZE_MEMORIES,
        "splitPortrait": SPLIT_PORTRAIT,
    }
    return jsonify({"assets": assets, "config": config})


@app.route("/api/thumbnail/<asset_id>")
def api_thumbnail(asset_id):
    """Proxy and optionally resize a thumbnail from Immich, with an in-memory LRU cache."""
    if not IMMICH_API_KEY:
        return "Unauthorized", 401

    # 1) LRU cache hit
    if THUMB_CACHE_SIZE > 0:
        with _thumb_cache_lock:
            if asset_id in _thumb_cache:
                _thumb_cache.move_to_end(asset_id)
                content, content_type = _thumb_cache[asset_id]
                return Response(
                    content,
                    content_type=content_type,
                    headers={"Cache-Control": "public, max-age=86400"},
                )

    url = "{}/api/assets/{}/thumbnail?size=preview".format(IMMICH_URL, asset_id)
    headers = {"x-api-key": IMMICH_API_KEY}

    try:
        resp = _http_session.get(url, headers=headers, timeout=30)
        logger.debug("Thumbnail proxy: %s -> %d", asset_id, resp.status_code)
        if resp.status_code != 200:
            return "Upstream error", resp.status_code

        content = resp.content
        content_type = resp.headers.get("Content-Type", "image/jpeg")

        # 2) Resize with Pillow when enabled and available
        if RESIZE_IMAGES and PIL_AVAILABLE:
            try:
                img = Image.open(BytesIO(content))
                img = ImageOps.exif_transpose(img)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.thumbnail(
                    (MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT),
                    Image.Resampling.LANCZOS,
                )
                out = BytesIO()
                img.save(out, format="JPEG", quality=IMAGE_QUALITY, optimize=True)
                content = out.getvalue()
                content_type = "image/jpeg"
            except Exception as exc:
                logger.warning("Pillow resize failed for %s, proxying raw image: %s", asset_id, exc)

        # 3) Store processed image in the LRU cache
        if THUMB_CACHE_SIZE > 0:
            with _thumb_cache_lock:
                _thumb_cache[asset_id] = (content, content_type)
                _thumb_cache.move_to_end(asset_id)
                while len(_thumb_cache) > THUMB_CACHE_SIZE:
                    _thumb_cache.popitem(last=False)

        return Response(
            content,
            content_type=content_type,
            headers={"Cache-Control": "public, max-age=86400"},
        )

    except requests.RequestException as exc:
        logger.error("Thumbnail proxy error: %s", exc)
        return "Proxy error", 502


@app.route("/api/asset/<asset_id>/details")
def api_asset_details(asset_id):
    """Fetch detailed asset info (people, location) on demand."""
    if not IMMICH_API_KEY:
        return jsonify({"error": "No API key"}), 401

    headers = {"x-api-key": IMMICH_API_KEY}
    detail_url = "{}/api/assets/{}".format(IMMICH_URL, asset_id)

    try:
        resp = _http_session.get(detail_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return jsonify({"error": "Not found"}), 404

        detail = resp.json()

        people_names = [p.get("name", "").strip() for p in (detail.get("people") or [])
                        if p.get("name", "").strip()]

        return jsonify({
            "people": people_names,
            "location": build_location(detail.get("exifInfo", {}) or {}),
        })

    except requests.RequestException as exc:
        logger.debug("Asset details error: %s", exc)
        return jsonify({"people": [], "location": ""})


@app.route("/api/debug")
def api_debug():
    """Debug endpoint to check Immich connection."""
    result = {
        "immich_url": IMMICH_URL,
        "api_key_set": bool(IMMICH_API_KEY),
        "album_id": IMMICH_ALBUM_ID,
        "interval": INTERVAL_SECONDS,
        "shuffle": SHUFFLE,
    }

    if not IMMICH_API_KEY or not IMMICH_ALBUM_ID:
        result["error"] = "Missing API key or album ID"
        return jsonify(result)

    assets = fetch_album_assets()
    result["assets_found"] = len(assets)
    if assets:
        result["thumbnail_url"] = "/api/thumbnail/" + assets[0]["id"]

    return jsonify(result)


@app.route("/api/time")
def api_time():
    """Return current server time with timezone."""
    tz = get_configured_timezone()
    now = datetime.now(timezone.utc).astimezone(tz)

    return jsonify({
        "timestamp": now.isoformat(),
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
        "day": now.day,
        "month": now.month,
        "year": now.year,
        "weekday": now.weekday(),
        "timezone": TIMEZONE or str(tz),
    })


@app.route("/api/weather")
def api_weather():
    """Fetch weather data from OpenWeatherMap API (cached for 15 minutes)."""
    global _weather_cache, _weather_cache_time

    if not WEATHER_API_KEY:
        return jsonify({"error": "No API key configured", "enabled": False})

    with _weather_cache_lock:
        if _weather_cache and (time.time() - _weather_cache_time) < WEATHER_CACHE_TTL:
            logger.debug("Returning cached weather data")
            return jsonify(_weather_cache)

    try:
        lat, lon = WEATHER_LAT_LONG.split(",")
    except ValueError:
        return jsonify({"error": "Invalid coordinates", "enabled": False})

    lang_map = {"pt": "pt_br", "en": "en", "es": "es", "fr": "fr", "de": "de"}
    owm_lang = lang_map.get(LANGUAGE, "en")

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat.strip(),
        "lon": lon.strip(),
        "appid": WEATHER_API_KEY,
        "units": UNIT_SYSTEM,
        "lang": owm_lang,
    }

    try:
        resp = _http_session.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            logger.error("Weather API error: %d", resp.status_code)
            return jsonify({"error": "API error", "enabled": True})

        data = resp.json()
        main = data.get("main", {}) or {}
        weather = (data.get("weather") or [{}])[0]
        temp = main.get("temp", 0)
        icon_code = weather.get("icon", "")
        unit_symbol = "°C" if UNIT_SYSTEM == "metric" else "°F"

        payload = {
            "enabled": True,
            "city": data.get("name", ""),
            "temp": round(temp),
            "tempMin": round(main.get("temp_min", 0)),
            "tempMax": round(main.get("temp_max", 0)),
            "feelsLike": round(main.get("feels_like", 0)),
            "unit": unit_symbol,
            "description": weather.get("description", ""),
            "iconId": icon_code,
            "iconUrl": "/api/weather-icon/" + icon_code,
        }

        with _weather_cache_lock:
            _weather_cache = payload
            _weather_cache_time = time.time()

        return jsonify(payload)

    except requests.RequestException as exc:
        logger.error("Weather fetch error: %s", exc)
        return jsonify({"error": str(exc), "enabled": True})


@app.route("/api/weather-icon/<icon_code>")
def api_weather_icon(icon_code):
    """Serve a cached weather icon if present, otherwise 404 (frontend uses native SVGs)."""
    icon_code = icon_code.replace("@2x", "")

    # Guard against path traversal in the icon code.
    if not re.fullmatch(r"[0-9a-zA-Z_-]+", icon_code):
        return "Icon not found", 404

    path = os.path.join(WEATHER_ICONS_DIR, "{}.png".format(icon_code))
    if not os.path.exists(path):
        return "Icon not found", 404

    with open(path, "rb") as f:
        content = f.read()

    return Response(
        content,
        content_type="image/png",
        headers={"Cache-Control": "public, max-age=604800"},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

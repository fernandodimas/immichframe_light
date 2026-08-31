"""
Immich Frame - Digital Photo Frame for Legacy Devices
=====================================================
A minimalist Flask app designed to run slideshow from an Immich album,
optimized for iOS 9.3.5 Safari and other legacy browsers.
"""

import os
import logging
import json
import random
from datetime import datetime

import requests
from flask import Flask, render_template, jsonify, Response

app = Flask(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Immich connection
IMMICH_URL = os.environ.get("IMMICH_URL", "http://localhost:2283").rstrip("/")
IMMICH_API_KEY = os.environ.get("IMMICH_API_KEY", "")
IMMICH_ALBUM_ID = os.environ.get("IMMICH_ALBUM_ID", "")

# Slideshow settings
INTERVAL_SECONDS = int(os.environ.get("INTERVAL_SECONDS", "20"))
TRANSITION_DURATION = float(os.environ.get("TRANSITION_DURATION", "2"))
SHUFFLE = os.environ.get("SHUFFLE", "true").lower() in ("true", "1", "yes")

# Display settings
SHOW_CLOCK = os.environ.get("SHOW_CLOCK", "true").lower() in ("true", "1", "yes")
CLOCK_FORMAT = os.environ.get("CLOCK_FORMAT", "HH:mm")
CLOCK_DATE_FORMAT = os.environ.get("CLOCK_DATE_FORMAT", "eeee, d 'de' MMMM 'de' yyyy")
SHOW_PROGRESS_BAR = os.environ.get("SHOW_PROGRESS_BAR", "true").lower() in ("true", "1", "yes")
SHOW_PHOTO_DATE = os.environ.get("SHOW_PHOTO_DATE", "true").lower() in ("true", "1", "yes")
SHOW_IMAGE_DESC = os.environ.get("SHOW_IMAGE_DESC", "true").lower() in ("true", "1", "yes")
SHOW_PEOPLE_DESC = os.environ.get("SHOW_PEOPLE_DESC", "true").lower() in ("true", "1", "yes")
SHOW_ALBUM_NAME = os.environ.get("SHOW_ALBUM_NAME", "true").lower() in ("true", "1", "yes")
SHOW_IMAGE_LOCATION = os.environ.get("SHOW_IMAGE_LOCATION", "true").lower() in ("true", "1", "yes")

# Style settings
PRIMARY_COLOR = os.environ.get("PRIMARY_COLOR", "#f5deb3")
SECONDARY_COLOR = os.environ.get("SECONDARY_COLOR", "#000000")
STYLE = os.environ.get("STYLE", "none")
BASE_FONT_SIZE = os.environ.get("BASE_FONT_SIZE", "17px")
IMAGE_LOCATION_FORMAT = os.environ.get("IMAGE_LOCATION_FORMAT", "City,State,Country")

logger.info("IMMICH_URL: %s", IMMICH_URL)
logger.info("IMMICH_ALBUM_ID: %s", IMMICH_ALBUM_ID or "NOT SET")
logger.info("INTERVAL: %ds, TRANSITION: %.1fs, SHUFFLE: %s", INTERVAL_SECONDS, TRANSITION_DURATION, SHUFFLE)


def fetch_album_assets():
    """Fetch asset list from Immich album API and return asset data."""
    if not IMMICH_API_KEY or not IMMICH_ALBUM_ID:
        logger.warning("IMMICH_API_KEY or IMMICH_ALBUM_ID not configured")
        return []

    headers = {"x-api-key": IMMICH_API_KEY}
    search_url = "{}/api/search/metadata".format(IMMICH_URL)
    payload = {
        "albumIds": [IMMICH_ALBUM_ID],
        "size": 1000,
    }

    logger.debug("Requesting: POST %s", search_url)

    try:
        resp = requests.post(search_url, json=payload, headers=headers, timeout=30)
        logger.debug("Response status: %d", resp.status_code)

        if resp.status_code != 200:
            logger.error("Immich returned HTTP %d: %s", resp.status_code, resp.text[:500])
            return []

        data = resp.json()
        assets = data.get("assets", {}).get("items", [])
        logger.debug("Found %d assets via search API", len(assets))

    except requests.RequestException as exc:
        logger.error("Failed to fetch album from Immich: %s", exc)
        return []
    except ValueError:
        logger.error("Invalid JSON response from Immich API")
        return []

    if not assets:
        logger.warning("Album '%s' has no assets", IMMICH_ALBUM_ID)
        return []

    result = []
    for asset in assets:
        asset_id = asset.get("id")
        if not asset_id:
            continue

        item = {
            "id": asset_id,
            "date": asset.get("localDateTime", asset.get("createdAt", "")),
            "description": asset.get("description", ""),
            "people": [],
            "location": "",
            "albumName": "",
        }

        # Extract people names
        people = asset.get("people", [])
        if people:
            item["people"] = [p.get("name", "") for p in people if p.get("name")]

        # Extract location
        city = asset.get("city", "")
        state = asset.get("state", "")
        country = asset.get("country", "")
        location_parts = []
        if "City" in IMAGE_LOCATION_FORMAT and city:
            location_parts.append(city)
        if "State" in IMAGE_LOCATION_FORMAT and state:
            location_parts.append(state)
        if "Country" in IMAGE_LOCATION_FORMAT and country:
            location_parts.append(country)
        item["location"] = ", ".join(location_parts)

        result.append(item)

    # Get album name
    try:
        album_url = "{}/api/albums/{}".format(IMMICH_URL, IMMICH_ALBUM_ID)
        album_resp = requests.get(album_url, headers=headers, timeout=15)
        if album_resp.status_code == 200:
            album_data = album_resp.json()
            album_name = album_data.get("albumName", "")
            for item in result:
                item["albumName"] = album_name
    except Exception as exc:
        logger.debug("Could not fetch album name: %s", exc)

    if SHUFFLE:
        random.shuffle(result)

    logger.info("Loaded %d assets from album", len(result))
    return result


@app.route("/")
def index():
    """Serve the main slideshow page."""
    return render_template("index.html")


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
        "showImageDesc": SHOW_IMAGE_DESC,
        "showPeopleDesc": SHOW_PEOPLE_DESC,
        "showAlbumName": SHOW_ALBUM_NAME,
        "showImageLocation": SHOW_IMAGE_LOCATION,
        "primaryColor": PRIMARY_COLOR,
        "secondaryColor": SECONDARY_COLOR,
        "style": STYLE,
        "baseFontSize": BASE_FONT_SIZE,
    }
    return jsonify({"assets": assets, "config": config})


@app.route("/api/thumbnail/<asset_id>")
def api_thumbnail(asset_id):
    """Proxy endpoint to fetch thumbnail from Immich with authentication."""
    if not IMMICH_API_KEY:
        return "Unauthorized", 401

    url = "{}/api/assets/{}/thumbnail?size=preview".format(IMMICH_URL, asset_id)
    headers = {"x-api-key": IMMICH_API_KEY}

    try:
        resp = requests.get(url, headers=headers, timeout=30, stream=True)
        logger.debug("Thumbnail proxy: %s -> %d", asset_id, resp.status_code)

        if resp.status_code != 200:
            return "Upstream error", resp.status_code

        content_type = resp.headers.get("Content-Type", "image/jpeg")
        return Response(
            resp.iter_content(chunk_size=8192),
            content_type=content_type,
            headers={"Cache-Control": "public, max-age=3600"},
        )

    except requests.RequestException as exc:
        logger.error("Thumbnail proxy error: %s", exc)
        return "Proxy error", 502


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
    """Return current server time."""
    now = datetime.now()
    return jsonify({
        "timestamp": now.isoformat(),
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
        "day": now.day,
        "month": now.month,
        "year": now.year,
        "weekday": now.weekday(),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

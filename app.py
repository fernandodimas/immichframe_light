"""
Immich Frame - Digital Photo Frame for Legacy Devices
=====================================================
A minimalist Flask app designed to run slideshow from an Immich album,
optimized for iOS 9.3.5 Safari and other legacy browsers.
"""

import os
import logging
import json

import requests
from flask import Flask, render_template, jsonify

app = Flask(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

IMMICH_URL = os.environ.get("IMMICH_URL", "http://localhost:2283").rstrip("/")
IMMICH_API_KEY = os.environ.get("IMMICH_API_KEY", "")
IMMICH_ALBUM_ID = os.environ.get("IMMICH_ALBUM_ID", "")
INTERVAL_SECONDS = int(os.environ.get("INTERVAL_SECONDS", "15"))

logger.info("IMMICH_URL: %s", IMMICH_URL)
logger.info("IMMICH_API_KEY: %s***", IMMICH_API_KEY[:6] if IMMICH_API_KEY else "NOT SET")
logger.info("IMMICH_ALBUM_ID: %s", IMMICH_ALBUM_ID or "NOT SET")
logger.info("INTERVAL_SECONDS: %s", INTERVAL_SECONDS)


def fetch_album_assets():
    """Fetch asset list from Immich album API and return thumbnail URLs."""
    if not IMMICH_API_KEY or not IMMICH_ALBUM_ID:
        logger.warning("IMMICH_API_KEY or IMMICH_ALBUM_ID not configured")
        return []

    url = "{}/api/albums/{}".format(IMMICH_URL, IMMICH_ALBUM_ID)
    headers = {"x-api-key": IMMICH_API_KEY}

    logger.debug("Requesting: GET %s", url)

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        logger.debug("Response status: %d", resp.status_code)
        logger.debug("Response headers: %s", dict(resp.headers))

        if resp.status_code != 200:
            logger.error("Immich returned HTTP %d: %s", resp.status_code, resp.text[:500])
            return []

        data = resp.json()
        logger.debug("Full API response keys: %s", list(data.keys()))
        logger.debug("Album name: %s", data.get("albumName", "N/A"))
        logger.debug("Asset count in response: %s", data.get("assetCount", "N/A"))

    except requests.RequestException as exc:
        logger.error("Failed to fetch album from Immich: %s", exc)
        return []
    except ValueError:
        logger.error("Invalid JSON response from Immich API")
        return []

    assets = data.get("assets", [])
    if not assets:
        logger.warning("Album '%s' has no assets. Full response: %s", IMMICH_ALBUM_ID, json.dumps(data, indent=2)[:1000])
        return []

    thumbnails = []
    for asset in assets:
        asset_id = asset.get("id")
        if asset_id:
            thumb_url = "{}/api/assets/{}/thumbnail?size=preview".format(
                IMMICH_URL, asset_id
            )
            thumbnails.append(thumb_url)

    logger.info("Loaded %d thumbnails from album", len(thumbnails))
    return thumbnails


@app.route("/")
def index():
    """Serve the main slideshow page."""
    thumbnails = fetch_album_assets()
    return render_template(
        "index.html",
        thumbnails=thumbnails,
        interval=INTERVAL_SECONDS,
    )


@app.route("/api/thumbnails")
def api_thumbnails():
    """API endpoint to refresh thumbnail list without page reload."""
    thumbnails = fetch_album_assets()
    return jsonify({"thumbnails": thumbnails, "interval": INTERVAL_SECONDS})


@app.route("/api/debug")
def api_debug():
    """Debug endpoint to check Immich connection."""
    result = {
        "immich_url": IMMICH_URL,
        "api_key_set": bool(IMMICH_API_KEY),
        "album_id": IMMICH_ALBUM_ID,
        "interval": INTERVAL_SECONDS,
    }

    if not IMMICH_API_KEY or not IMMICH_ALBUM_ID:
        result["error"] = "Missing API key or album ID"
        return jsonify(result)

    url = "{}/api/albums/{}".format(IMMICH_URL, IMMICH_ALBUM_ID)
    headers = {"x-api-key": IMMICH_API_KEY}

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        result["status_code"] = resp.status_code
        result["response"] = resp.json()
    except Exception as exc:
        result["error"] = str(exc)

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

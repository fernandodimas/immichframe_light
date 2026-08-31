"""
Immich Frame - Digital Photo Frame for Legacy Devices
=====================================================
A minimalist Flask app designed to run slideshow from an Immich album,
optimized for iOS 9.3.5 Safari and other legacy browsers.
"""

import os
import logging

import requests
from flask import Flask, render_template, jsonify

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IMMICH_URL = os.environ.get("IMMICH_URL", "http://localhost:2283").rstrip("/")
IMMICH_API_KEY = os.environ.get("IMMICH_API_KEY", "")
IMMICH_ALBUM_ID = os.environ.get("IMMICH_ALBUM_ID", "")
INTERVAL_SECONDS = int(os.environ.get("INTERVAL_SECONDS", "15"))


def fetch_album_assets():
    """Fetch asset list from Immich album API and return thumbnail URLs."""
    if not IMMICH_API_KEY or not IMMICH_ALBUM_ID:
        logger.warning("IMMICH_API_KEY or IMMICH_ALBUM_ID not configured")
        return []

    url = "{}/api/albums/{}".format(IMMICH_URL, IMMICH_ALBUM_ID)
    headers = {"x-api-key": IMMICH_API_KEY}

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.error("Failed to fetch album from Immich: %s", exc)
        return []
    except ValueError:
        logger.error("Invalid JSON response from Immich API")
        return []

    assets = data.get("assets", [])
    if not assets:
        logger.warning("Album '%s' has no assets", IMMICH_ALBUM_ID)
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

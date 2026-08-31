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
from flask import Flask, render_template, jsonify, Response

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
    """Fetch asset list from Immich album API and return asset IDs."""
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

    asset_ids = []
    for asset in assets:
        asset_id = asset.get("id")
        if asset_id:
            asset_ids.append(asset_id)

    logger.info("Loaded %d assets from album", len(asset_ids))
    return asset_ids


@app.route("/")
def index():
    """Serve the main slideshow page."""
    return render_template("index.html", interval=INTERVAL_SECONDS)


@app.route("/api/slideshow")
def api_slideshow():
    """API endpoint to get slideshow data for JavaScript."""
    asset_ids = fetch_album_assets()
    return jsonify({"assets": asset_ids, "interval": INTERVAL_SECONDS})


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
    }

    if not IMMICH_API_KEY or not IMMICH_ALBUM_ID:
        result["error"] = "Missing API key or album ID"
        return jsonify(result)

    asset_ids = fetch_album_assets()
    result["assets_found"] = len(asset_ids)
    if asset_ids:
        result["thumbnail_url"] = "/api/thumbnail/" + asset_ids[0]

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

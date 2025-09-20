import os
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

# -----------------------
# Basic endpoints
# -----------------------

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "alive"}), 200

@app.route("/time", methods=["GET"])
def current_time():
    """Return current server time (UTC)"""
    now = datetime.utcnow().isoformat() + "Z"
    return jsonify({"utc_time": now, "timestamp": time.time()}), 200

@app.route("/transform", methods=["POST"])
def transform():
    """
    Transform endpoint.
    Expected JSON body: {"text": "<string>", "mode": "upper"|"lower"|"strip"}
    """
    payload = request.json or {}
    text = payload.get("text", "")
    mode = payload.get("mode", "upper").lower()

    if mode == "upper":
        result = text.upper()
    elif mode == "lower":
        result = text.lower()
    elif mode == "strip":
        result = " ".join(text.split())
    else:
        return jsonify({"error": "invalid mode"}), 400

    return jsonify({"original": text, "result": result, "mode": mode}), 200

# -----------------------
# Echo + root (kept)
# -----------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Hello Chief! Your Flask API is live 🚀"}), 200

@app.route("/echo", methods=["POST"])
def echo():
    data = request.json
    return jsonify({"you_sent": data, "status": "success"}), 200

# -----------------------
# Weather integration (optional)
# -----------------------
OPENWEATHER_KEY = os.environ.get("OPENWEATHER_API_KEY")  # set in Render dashboard

@app.route("/weather", methods=["GET"])
def weather():
    """
    Query example: /weather?city=London&units=metric
    This uses OpenWeatherMap API and requires OPENWEATHER_API_KEY in env.
    """
    city = request.args.get("city")
    units = request.args.get("units", "metric")

    if not city:
        return jsonify({"error": "missing 'city' parameter"}), 400

    if not OPENWEATHER_KEY:
        return jsonify({"error": "OPENWEATHER_API_KEY not configured on server"}), 500

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "units": units, "appid": OPENWEATHER_KEY}
    resp = requests.get(url, params=params, timeout=10)

    if resp.status_code != 200:
        return jsonify({"error": "failed to fetch weather", "details": resp.text}), resp.status_code

    data = resp.json()
    result = {
        "city": data.get("name"),
        "weather": data.get("weather"),
        "main": data.get("main"),
        "raw": data
    }
    return jsonify(result), 200

# -----------------------
# Naive summarizer (no external keys)
# -----------------------

def naive_summary(text, max_sentences=3):
    """
    Extremely simple extractive summarizer:
    returns the first N sentences. Good enough as demo & avoids external API keys.
    """
    # split by sentence-ending punctuation naive approach
    import re
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    summary = " ".join(parts[:max_sentences]) if parts else ""
    return summary

@app.route("/summarize", methods=["POST"])
def summarize():
    """
    POST JSON body:
    { "text": "<long text>", "max_sentences": 2 }
    """
    payload = request.json or {}
    text = payload.get("text", "")
    if not text:
        return jsonify({"error": "missing 'text' in body"}), 400

    try:
        max_s = int(payload.get("max_sentences", 3))
    except Exception:
        max_s = 3

    summary = naive_summary(text, max_sentences=max_s)
    return jsonify({"summary": summary, "length": len(summary.split()), "max_sentences": max_s}), 200

# -----------------------
# Simple OpenAPI / Swagger UI (static)
# -----------------------
OPENAPI_SPEC = {
  "openapi": "3.0.0",
  "info": {"title": "Flask Chief API", "version": "1.0.0"},
  "paths": {
    "/": {"get": {"summary": "Root", "responses": {"200": {"description": "OK"}}}},
    "/health": {"get": {"summary": "Health", "responses": {"200": {"description": "OK"}}}},
    "/time": {"get": {"summary": "Server time", "responses": {"200": {"description": "OK"}}}},
    "/transform": {"post": {"summary": "Transform text", "responses": {"200": {"description": "OK"}}}},
    "/weather": {"get": {"summary": "Weather (requires key)", "responses": {"200": {"description": "OK"}}}},
    "/summarize": {"post": {"summary": "Summarize text", "responses": {"200": {"description": "OK"}}}}
  }
}

@app.route("/openapi.json", methods=["GET"])
def openapi():
    return jsonify(OPENAPI_SPEC), 200

# Very small HTML page that loads swagger UI from CDN and points it at /openapi.json
SWAGGER_HTML = """
<!doctype html>
<html>
  <head>
    <title>API Docs</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@4/swagger-ui.css">
  </head>
  <body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@4/swagger-ui-bundle.js"></script>
  <script>
    const ui = SwaggerUIBundle({ url: "/openapi.json", dom_id: '#swagger-ui' })
  </script>
  </body>
</html>
"""

@app.route("/docs", methods=["GET"])
def docs():
    return render_template_string(SWAGGER_HTML)

# -----------------------
# Run
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

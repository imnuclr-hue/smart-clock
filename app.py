#!/usr/bin/env python3
"""
Raspberry Pi Clock Display
Serves a full-screen clock with BME280 sensor data + weather forecast.
"""

from flask import Flask, jsonify, render_template_string
import threading
import time
import json
import os
import requests
from datetime import datetime

app = Flask(__name__)

# ── Sensor state ────────────────────────────────────────────────────────────
sensor_data = {
    "temperature": None,
    "humidity": None,
    "pressure": None,
    "light": None,
    "error": None,
}

weather_data = {
    "forecast": [],
    "current": None,
    "location": None,
    "error": None,
    "last_updated": None,
}

# ── Config ───────────────────────────────────────────────────────────────────
# Set your Open-Meteo location (free, no API key needed) 
# 51.2667091802614, 0.2736364823066489
LATITUDE  = 51.2667   # Ivy Hatch (Crown House)
LONGITUDE = 0.2736
LOCATION_NAME = "Ivy Hatch"

# How often to poll sensors (seconds)
SENSOR_INTERVAL  = 5
WEATHER_INTERVAL = 600  # 10 minutes


# ── BME280 reader ─────────────────────────────────────────────────────────────
def read_bme280():
    try:
        import board, busio
        import adafruit_bme280.basic as adafruit_bme280
        i2c = busio.I2C(board.SCL, board.SDA)
        bme = adafruit_bme280.Adafruit_BME280_I2C(i2c)
        return {
            "temperature": round(bme.temperature, 1),
            "humidity":    round(bme.humidity, 1),
            "pressure":    round(bme.pressure, 1),
        }
    except Exception as e:
        return {"error": f"BME280: {e}"}


# ── BH1750 reader ─────────────────────────────────────────────────────────────
def read_bh1750():
    try:
        import board, busio
        import adafruit_bh1750
        i2c = busio.I2C(board.SCL, board.SDA)
        sensor = adafruit_bh1750.BH1750(i2c)
        return {"light": round(sensor.lux, 1)}
    except Exception as e:
        return {"light_error": f"BH1750: {e}"}


# ── Sensor polling thread ─────────────────────────────────────────────────────
def sensor_loop():
    global sensor_data
    while True:
        bme = read_bme280()
        bh  = read_bh1750()
        if "error" in bme:
            sensor_data["error"] = bme["error"]
        else:
            sensor_data.update(bme)
            sensor_data["error"] = None
        if "light" in bh:
            sensor_data["light"] = bh["light"]
        time.sleep(SENSOR_INTERVAL)


# ── Weather fetch (Open-Meteo — free, no key) ─────────────────────────────────
WMO_CODES = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"), 2: ("Partly cloudy", "⛅"), 3: ("Overcast", "☁️"),
    45: ("Foggy", "🌫️"), 48: ("Icy fog", "🌫️"),
    51: ("Light drizzle", "🌦️"), 53: ("Drizzle", "🌦️"), 55: ("Heavy drizzle", "🌧️"),
    61: ("Slight rain", "🌧️"), 63: ("Rain", "🌧️"), 65: ("Heavy rain", "🌧️"),
    71: ("Slight snow", "🌨️"), 73: ("Snow", "❄️"), 75: ("Heavy snow", "❄️"),
    77: ("Snow grains", "🌨️"),
    80: ("Showers", "🌦️"), 81: ("Rain showers", "🌧️"), 82: ("Violent showers", "⛈️"),
    85: ("Snow showers", "🌨️"), 86: ("Heavy snow showers", "❄️"),
    95: ("Thunderstorm", "⛈️"), 96: ("Thunderstorm+hail", "⛈️"), 99: ("Thunderstorm+hail", "⛈️"),
}

def fetch_weather():
    global weather_data
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={LATITUDE}&longitude={LONGITUDE}"
        f"&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum"
        f"&current_weather=true"
        f"&timezone=Europe%2FLondon"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        d = r.json()
        cw = d["current_weather"]
        code = cw["weathercode"]
        desc, icon = WMO_CODES.get(code, ("Unknown", "🌡️"))
        weather_data["current"] = {
            "temp":      round(cw["temperature"], 1),
            "windspeed": round(cw["windspeed"], 1),
            "desc":      desc,
            "icon":      icon,
        }
        daily = d["daily"]
        forecast = []
        for i in range(min(5, len(daily["time"]))):
            c2, i2 = WMO_CODES.get(daily["weathercode"][i], ("Unknown", "🌡️"))
            forecast.append({
                "date":    daily["time"][i],
                "max":     round(daily["temperature_2m_max"][i], 1),
                "min":     round(daily["temperature_2m_min"][i], 1),
                "precip":  round(daily["precipitation_sum"][i], 1),
                "desc":    c2,
                "icon":    i2,
            })
        weather_data["forecast"]     = forecast
        weather_data["location"]     = LOCATION_NAME
        weather_data["error"]        = None
        weather_data["last_updated"] = datetime.now().isoformat()
    except Exception as e:
        weather_data["error"] = str(e)

def weather_loop():
    while True:
        fetch_weather()
        time.sleep(WEATHER_INTERVAL)


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/api/sensors")
def api_sensors():
    return jsonify(sensor_data)

@app.route("/api/weather")
def api_weather():
    return jsonify(weather_data)

@app.route("/")
def index():
    with open(os.path.join(os.path.dirname(__file__), "templates", "clock.html")) as f:
        return f.read()


# ── Boot ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    threading.Thread(target=sensor_loop,  daemon=True).start()
    threading.Thread(target=weather_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8080, debug=False)

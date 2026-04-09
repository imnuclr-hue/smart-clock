# 🕐 Pi Clock Display

A full-screen clock for Raspberry Pi with:
- 12h/24h toggle (tap the button, persists across reboots)
- BME280 indoor sensor: temperature, humidity, pressure
- BH1750 light sensor: ambient lux bar
- Open-Meteo weather forecast (free, no API key) with offline fallback

---

## Hardware

| Component | Connection |
|-----------|------------|
| BME280    | I²C (SDA/SCL, 3.3V, GND) |
| BH1750    | I²C (SDA/SCL, 3.3V, GND) |
| Touchscreen | DSI / HDMI (any) |

Both sensors share the I²C bus — just wire them in parallel.

---

## 1. Enable I²C

```bash
sudo raspi-config
# Interface Options → I2C → Enable
```

---

## 2. Install dependencies

```bash
pip3 install -r requirements.txt --break-system-packages
```

---

## 3. Configure your location

Edit `app.py` and set your coordinates and location name:

```python
LATITUDE      = 51.4619    # your latitude
LONGITUDE     = -0.3320    # your longitude
LOCATION_NAME = "Hounslow" # display name
```

---

## 4. Run it

```bash
python3 app.py
```

Then open **http://localhost:8080** in Chromium (or any browser).

For a kiosk-style fullscreen launch, add this to your autostart:

```bash
chromium-browser --kiosk --app=http://localhost:8080 --noerrdialogs --disable-infobars
```

---

## 5. Autostart on boot (systemd)

```bash
# Copy the app
cp -r pi-clock/ /home/pi/pi-clock

# Install the service
sudo cp pi-clock.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pi-clock
sudo systemctl start pi-clock

# Check it's running
sudo systemctl status pi-clock
```

Then set Chromium to open on login pointing to http://localhost:8080.

---

## Offline mode

Weather fetches fail gracefully — the app will display a "No internet connection" notice and continue showing the clock and indoor sensor data normally. It retries every 10 minutes.

---

## File structure

```
pi-clock/
├── app.py              # Flask server + sensor polling
├── requirements.txt
├── pi-clock.service    # systemd unit
└── templates/
    └── clock.html      # Full-screen UI
```

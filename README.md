# MeteoMate ☀️🌧️

A fast, human-friendly terminal weather CLI using **Open-Meteo** (no API key).  
Shows current conditions and a clean multi-day forecast with readable, emoji-enhanced output.

> No sign-ups, no API keys — just weather.

---

## ✨ Features
- **Current weather**: temperature, feels-like, humidity, wind, condition
- **Forecast**: N days (default **3**, up to **16**)
- **Smart quips**: playful remarks based on rain/snow/storm/heat/wind
- **ANSI colors + emojis** (disable with `NO_COLOR=1`)
- **No API key** — uses Open-Meteo geocoding + forecast

---

## 📦 Requirements
- Python **3.8+** (recommended)
- `requests:`

```bash
pip install requests
```

## ▶️ Usage
First, install the dependency and run the commands you need:

pip install requests

# Current weather
python weather.py current "Istanbul"

# 3-day forecast (default)
python weather.py forecast "Istanbul"

# Custom number of days (up to 16)
python weather.py forecast "Istanbul" --days 5
python weather.py forecast "Istanbul" -d 5

# Disable colors (plain output)
NO_COLOR=1 python weather.py forecast "Istanbul"         # macOS/Linux
$env:NO_COLOR=1; python weather.py forecast "Istanbul"   # Windows PowerShell

import argparse
import os
import sys
import requests
import random
from datetime import datetime

def supports_color():
    return (os.getenv("NO_COLOR") is None) and (
        sys.stdout.isatty() and (os.name != "nt" or "WT_SESSION" in os.environ or "ANSICON" in os.environ)
    )
COLOR = supports_color()
def c(s, code): return f"\033[{code}m{s}\033[0m" if COLOR else s
def bold(s): return c(s, "1")
def blue(s): return c(s, "34")
def cyan(s): return c(s, "36")
def green(s): return c(s, "32")
def yellow(s): return c(s, "33")
def red(s): return c(s, "31")
def dim(s): return c(s, "2")

WMO = {
    0: ("Clear sky", "☀️"),
    1: ("Mostly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Depositing rime fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Moderate drizzle", "🌦️"),
    55: ("Dense drizzle", "🌧️"),
    56: ("Light freezing drizzle", "🌧️"),
    57: ("Dense freezing drizzle", "🌧️"),
    61: ("Slight rain", "🌧️"),
    63: ("Rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    66: ("Light freezing rain", "🌧️"),
    67: ("Heavy freezing rain", "🌧️"),
    71: ("Slight snow fall", "🌨️"),
    73: ("Snow fall", "🌨️"),
    75: ("Heavy snow fall", "❄️"),
    77: ("Snow grains", "🌨️"),
    80: ("Rain showers", "🌦️"),
    81: ("Heavy rain showers", "🌧️"),
    82: ("Violent rain showers", "⛈️"),
    85: ("Snow showers", "🌨️"),
    86: ("Heavy snow showers", "❄️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm, slight hail", "⛈️"),
    99: ("Thunderstorm, heavy hail", "⛈️"),
}

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

RAIN_CODES = {51,53,55,56,57,61,63,65,66,67,80,81,82}
SNOW_CODES = {71,73,75,77,85,86}
STORM_CODES = {95,96,99}

def is_rainy(code: int) -> bool:
    return code in RAIN_CODES

def is_snowy(code: int) -> bool:
    return code in SNOW_CODES

def is_stormy(code: int) -> bool:
    return code in STORM_CODES

def is_cloudy(code: int) -> bool:
    return code in {2,3,45,48}

def is_clearish(code: int) -> bool:
    return code in {0,1}

def is_hot(temp: float | None) -> bool:
    return temp is not None and temp >= 28.0

def is_cold(temp: float | None) -> bool:
    return temp is not None and temp <= 5.0

def is_windy(wind_kmh: float | None) -> bool:
    return wind_kmh is not None and wind_kmh >= 30.0

GENERIC_QUIPS = [
    "Weather brought to you by Mother Nature™",
    "Perfect time for a tiny walk 🚶",
    "Hydrate and dominate 💧",
    "Skies change, vibes stay ✨",
]

def choose_quip_current(code: int, temp: float | None, wind: float | None) -> str:
    if is_stormy(code):
        return "Thunder buddies? Maybe stay indoors today ⛈️"
    if is_rainy(code):
        return "Umbrella: highly recommended ☔"
    if is_snowy(code):
        return "Build a tiny snowman for me ⛄"
    if is_windy(wind):
        return "Hold onto your hat — it’s breezy 🎩💨"
    if is_hot(temp):
        return "Sunscreen > regrets. Stay cool 😎"
    if is_cold(temp):
        return "Layers on layers — stay warm 🧣"
    if is_clearish(code):
        return "Sun’s out, serotonin’s up 🌤️"
    if is_cloudy(code):
        return "Cloudy mood? Nah, cozy vibe ☁️"
    return random.choice(GENERIC_QUIPS)

def choose_quip_daily(code: int, precip_prob: float | None, day_index: int) -> str:

    if is_stormy(code):
        return "⚠️ stormy"
    if is_rainy(code):
        if precip_prob is not None and precip_prob >= 60:
            return "bring umbrella"
        return "light showers"
    if is_snowy(code):
        return "bundle up"
    if code in {0,1}:
        return "sunglasses?"
    if code in {2,3}:
        return "cloud cover"

    return "maybe picnic?" if day_index % 3 == 0 else "you got this"

def geocode_city(city: str):
    """Return (name, country, lat, lon, timezone) for the best match."""
    params = {"name": city, "count": 1, "language": "en", "format": "json"}
    r = requests.get(GEOCODE_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    results = data.get("results") or []
    if not results:
        raise ValueError(f"No results for city: {city}")
    res = results[0]
    return (
        res.get("name"),
        res.get("country"),
        res["latitude"],
        res["longitude"],
        res.get("timezone", "auto"),
    )

def get_weather(lat, lon, timezone="auto", days=3):
    """Fetch current and daily forecast."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": timezone,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "forecast_days": max(1, min(16, days)),
    }
    r = requests.get(FORECAST_URL, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def fmt_temp(t):
    if t is None:
        return "—"
    try:
        return f"{float(t):.1f}°C"
    except Exception:
        return f"{t}°C"

def print_current(loc_label, current):
    code = int(current.get("weather_code", -1))
    desc, emoji = WMO.get(code, ("Unknown", "❔"))
    temp = current.get("temperature_2m")
    feels = current.get("apparent_temperature")
    rh = current.get("relative_humidity_2m")
    wind = current.get("wind_speed_10m")
    time = current.get("time")
    t = datetime.fromisoformat(time).strftime("%Y-%m-%d %H:%M") if time else ""
    print(bold(blue(f"\n📍 {loc_label} — Current Weather")))
    print(dim(f"   {t}"))
    print(f"   {emoji} {desc}")
    print(f"   🌡️ {fmt_temp(temp)}  (feels {fmt_temp(feels)})")
    print(f"   💧 {rh}%   🧭 wind {wind} km/h")

    print(dim("   " + choose_quip_current(code, temp, wind)))

def print_forecast(daily, days):
    print(bold(cyan(f"\n📅 {days}-Day Forecast")))

    dates = daily.get("time", [])
    wcodes = daily.get("weather_code", [])
    tmax = daily.get("temperature_2m_max", [])
    tmin = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_probability_max", [])

    for i in range(min(days, len(dates))):
        d = dates[i]
        code = int(wcodes[i]) if i < len(wcodes) else -1
        desc, emoji = WMO.get(code, ("Unknown", "❔"))
        hi = tmax[i] if i < len(tmax) else None
        lo = tmin[i] if i < len(tmin) else None
        pp = precip[i] if i < len(precip) else None
        dayname = datetime.fromisoformat(d).strftime("%a %b %d")
        quip = choose_quip_daily(code, pp, i)
        tail = f" • {quip}" if quip else ""
        print(f"   {dayname}: {emoji} {desc}  ⬆ {fmt_temp(hi)}  ⬇ {fmt_temp(lo)}  ☔ {pp}%{dim(tail)}")

def handle_current(city):
    name, country, lat, lon, tz = geocode_city(city)
    data = get_weather(lat, lon, tz, days=1)
    loc_label = f"{name}, {country}"
    print_current(loc_label, data.get("current", {}))

def handle_forecast(city, days):
    name, country, lat, lon, tz = geocode_city(city)
    data = get_weather(lat, lon, tz, days=days)
    loc_label = f"{name}, {country}"
    print_current(loc_label, data.get("current", {}))
    print_forecast(data.get("daily", {}), days)

def main():
    parser = argparse.ArgumentParser(
        description="Weather CLI (Open-Meteo): current conditions + multi-day forecast"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_now = sub.add_parser("current", help="Show current weather for a city")
    p_now.add_argument("city", type=str, help='City name, e.g. "Istanbul"')

    p_fc = sub.add_parser("forecast", help="Show N-day forecast for a city (default 3)")
    p_fc.add_argument("city", type=str, help='City name, e.g. "Istanbul"')
    p_fc.add_argument("--days", "-d", type=int, default=3, help="Number of days (1–16)")

    args = parser.parse_args()

    try:
        if args.command == "current":
            handle_current(args.city)
        elif args.command == "forecast":
            handle_forecast(args.city, args.days)
    except requests.RequestException as e:
        print(red(f"Network error: {e}"))
        sys.exit(1)
    except ValueError as e:
        print(red(str(e)))
        sys.exit(2)

if __name__ == "__main__":
    main()
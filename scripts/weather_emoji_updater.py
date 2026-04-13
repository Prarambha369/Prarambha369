import os
import re
import requests
from datetime import datetime

# Configuration
GITHUB_USERNAME = "Prarambha369"
README_FILE = "README.md"
LOCATION = "Butwal,NP"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Fallback data if API fails or key is missing
def get_fallback_data():
    now = datetime.utcnow()
    hour = now.hour
    time_emoji = get_time_emoji(hour)
    time_label = get_time_label(hour)
    return {
        "time_emoji": time_emoji,
        "time_label": time_label,
        "weather_emoji": "🌤️",
        "condition": "Data Unavailable",
        "temp": "--",
        "humidity": "--",
        "is_fallback": True
    }

def get_time_emoji(hour):
    if 4 <= hour < 6: return "🌅"  # Dawn
    if 6 <= hour < 11: return "☀️" # Morning
    if 11 <= hour < 15: return "🌞" # Noon
    if 15 <= hour < 18: return "🌇" # Afternoon
    if 18 <= hour < 21: return "🌆" # Evening
    if 21 <= hour < 24: return "🌙" # Night
    return "🌌" # Midnight

def get_time_label(hour):
    if 4 <= hour < 6: return "Dawn"
    if 6 <= hour < 11: return "Morning"
    if 11 <= hour < 15: return "Noon"
    if 15 <= hour < 18: return "Afternoon"
    if 18 <= hour < 21: return "Evening"
    if 21 <= hour < 24: return "Night"
    return "Midnight"

def get_weather_emoji(condition_id, cloudiness):
    # Thunderstorm
    if 200 <= condition_id < 300: return "⛈️"
    # Drizzle / Rain
    if 300 <= condition_id < 600: return "🌧️"
    # Snow
    if 600 <= condition_id < 700: return "❄️"
    # Atmosphere (Fog, Mist, Smoke)
    if 700 <= condition_id < 800: return "🌫️"
    # Clear
    if condition_id == 800: 
        return "☀️" if cloudiness < 20 else "🌤️"
    # Clouds
    if 801 <= condition_id < 900:
        if cloudiness < 40: return "🌤️"
        if cloudiness < 80: return "⛅"
        return "☁️"
    return "🌍"

def fetch_weather_data():
    if not OPENWEATHER_API_KEY:
        print("⚠️ No API Key found. Using fallback data.")
        return get_fallback_data()

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={LOCATION}&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        now = datetime.utcnow()
        # Adjust for Nepal Time (UTC + 5:45) roughly for logic if needed, 
        # but OpenWeather usually returns local sunrise/sunset. 
        # We will use UTC hour + 5.75 for local time logic
        local_hour = (now.hour + 5) % 24 
        # Rough adjustment for the 45 mins, good enough for emoji logic
        if now.minute > 15: 
             # Simple shift logic, refined below
             pass 
        
        # Better: Use timestamp from API for sunrise/sunset comparison or just UTC offset
        # Nepal is UTC+5:45. 
        utc_offset = 5.75
        local_dt = datetime.utcnow().timestamp() + (utc_offset * 3600)
        local_hour = datetime.fromtimestamp(local_dt).hour

        weather = data['weather'][0]
        main = data['main']
        
        condition_id = weather['id']
        cloudiness = data.get('clouds', {}).get('all', 0)
        
        return {
            "time_emoji": get_time_emoji(local_hour),
            "time_label": get_time_label(local_hour),
            "weather_emoji": get_weather_emoji(condition_id, cloudiness),
            "condition": weather['description'].title(),
            "temp": f"{main['temp']}°C",
            "humidity": f"{main['humidity']}%",
            "is_fallback": False
        }
    except Exception as e:
        print(f"⚠️ Error fetching weather: {e}. Using fallback.")
        return get_fallback_data()

def update_readme(data):
    with open(README_FILE, 'r') as f:
        content = f.read()

    # The marker we will look for: <!-- WEATHER_STATUS: ... -->
    # We replace the whole line or block between markers
    
    start_marker = "<!-- WEATHER_START -->"
    end_marker = "<!-- WEATHER_END -->"
    
    # Construct the new status line
    if data['is_fallback']:
        status_text = f"{data['time_emoji']} {data['time_label']} in Butwal 🇳🇵 · ☁️ Waiting for API Key"
    else:
        status_text = f"{data['time_emoji']} {data['time_label']} · {data['weather_emoji']} {data['condition']} · 🌡️ {data['temp']} · 💧 {data['humidity']}"

new_block = f"{start_marker}\n<div align=\"center\">\n\n**Current Status:** {status_text}\n\n</div>\n<!-- WEATHER_END -->"

    # Regex to find existing block
    pattern = re.compile(f"{re.escape(start_marker)}.*?{re.escape(end_marker)}", re.DOTALL)
    
    if pattern.search(content):
        new_content = pattern.sub(new_block, content)
    else:
        print("⚠️ Markers not found! Appending to top of body or failing.")
        # Fallback: Just append after the first header if markers missing
        # But ideally, user must add markers first.
        return False

    with open(README_FILE, 'w') as f:
        f.write(new_content)
    
    print(f"✅ README updated: {status_text}")
    return True

if __name__ == "__main__":
    weather_data = fetch_weather_data()
    update_readme(weather_data)

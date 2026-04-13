import os
import re
import requests
import random
from datetime import datetime

# Configuration
GITHUB_USERNAME = "Prarambha369"
README_FILE = "README.md"
LOCATION = "Butwal,NP"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# --- STUDENT & NEPALI CONTEXT DATA ---

def get_student_slang(hour, is_weekend, is_holiday, is_exam_season):
    """Returns a random student/developer slang based on context."""
    
    # Base slangs by time of day
    time_slangs = {
        "dawn": ["Booting OS", "Morning Coffee", "Hello World", "Waking Up Daemons"],
        "morning": ["Compiling Code", "Attending Virtual Class", "Git Pushing", "Debugging Life"],
        "noon": ["Peak CPU Usage", "Lunch Break", "Merge Conflicts", "Stack Overflowing"],
        "afternoon": ["Refactoring Spaghetti", "LeetCode Grinding", "Building Projects", "Caffeine Injection"],
        "evening": ["Deploying to Prod", "Group Project Chaos", "Committing Changes", "Pushing Deadlines"],
        "night": ["Late Night Grind", "Bug Hunting", "Ramen & Code", "Insomnia Coding"],
        "midnight": ["Garbage Collection", "System Sleep", "Dreaming in Binary", "Recharging Batteries"]
    }

    # Special Context Overrides
    if is_holiday:
        return random.choice([
            "Touching Grass", "Offline Mode", "Festival Mode Activated", 
            "No Code Today", "Celebrating Dashain/Tihar", "Family Time"
        ])
    
    if is_weekend:
        return random.choice([
            "Weekend Hackathon", "Side Project Mode", "Gaming Session", 
            "Open Source Contributing", "Learning New Stack", "Restoring RAM"
        ])

    if is_exam_season:
        return random.choice([
            "Exam Mode: ON", "Cramming Syllabus", "Mem Leaks in Brain", 
            "Studying Algorithms", "Skipping Sleep for Grades", "Finals Week"
        ])

    # Normal Student Life
    period = "morning"
    if 4 <= hour < 6: period = "dawn"
    elif 6 <= hour < 11: period = "morning"
    elif 11 <= hour < 15: period = "noon"
    elif 15 <= hour < 18: period = "afternoon"
    elif 18 <= hour < 21: period = "evening"
    elif 21 <= hour < 24: period = "night"
    else: period = "midnight"

    return random.choice(time_slangs[period])

def check_nepali_context(local_dt):
    """Checks for Nepali holidays, weekends, and exam seasons."""
    is_weekend = local_dt.weekday() >= 4  # Friday (4) & Saturday (5) are weekends in Nepal
    
    day = local_dt.day
    month = local_dt.month
    
    # Approximate Exam Seasons for Nepali Students (Often Mangshir/Poush or Jestha/Ashad)
    # Adjust these months based on your specific academic calendar
    is_exam_season = month in [5, 6, 11, 12] # May/June or Nov/Dec approx

    # Simple AD/Nepali Festival Checks (Approximate Gregorian dates for major festivals)
    # For precise BS dates, you'd need the 'nepali-datetime' library installed in the action
    is_holiday = False
    holiday_name = ""

    # Dashain/Tihar approx (Sept/Oct)
    if month == 10 and 15 <= day <= 30: 
        is_holiday = True
        holiday_name = "Dashain/Tihar Season"
    # Nepali New Year approx (Mid April)
    elif month == 4 and day >= 10:
        is_holiday = True
        holiday_name = "Nepali New Year"
    # Christmas
    elif month == 12 and day == 25:
        is_holiday = True
        holiday_name = "Christmas"
        
    return is_weekend, is_holiday, is_exam_season

# --- EXISTING HELPER FUNCTIONS ---

def get_fallback_data():
    now = datetime.utcnow()
    utc_offset = 5.75
    local_dt = datetime.fromtimestamp(now.timestamp() + (utc_offset * 3600))
    hour = local_dt.hour
    
    is_weekend, is_holiday, is_exam_season = check_nepali_context(local_dt)
    status_label = get_student_slang(hour, is_weekend, is_holiday, is_exam_season)

    return {
        "status_label": status_label,
        "weather_emoji": "🌤️",
        "condition": "Data Unavailable",
        "temp": "--",
        "humidity": "--",
        "is_fallback": True
    }

def get_weather_emoji(condition_id, cloudiness):
    if 200 <= condition_id < 300: return "⛈️"
    if 300 <= condition_id < 600: return "🌧️"
    if 600 <= condition_id < 700: return "❄️"
    if 700 <= condition_id < 800: return "🌫️"
    if condition_id == 800: 
        return "☀️" if cloudiness < 20 else "🌤️"
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
        utc_offset = 5.75
        local_dt = datetime.fromtimestamp(now.timestamp() + (utc_offset * 3600))
        hour = local_dt.hour

        weather = data['weather'][0]
        main = data['main']
        
        condition_id = weather['id']
        cloudiness = data.get('clouds', {}).get('all', 0)
        
        is_weekend, is_holiday, is_exam_season = check_nepali_context(local_dt)
        status_label = get_student_slang(hour, is_weekend, is_holiday, is_exam_season)

        return {
            "status_label": status_label,
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

    start_marker = "<!-- WEATHER_START -->"
    end_marker = "<!-- WEATHER_END -->"
    
    if data['is_fallback']:
        status_text = f"**{data['status_label']}** in Butwal 🇳🇵 · ☁️ Waiting for API Key"
    else:
        status_text = f"**{data['status_label']}** · {data['weather_emoji']} {data['condition']} · 🌡️ {data['temp']} · 💧 {data['humidity']}"

    new_block = f"{start_marker}\n<div align=\"center\">\n\n> Current Status: {status_text}\n\n</div>\n<!-- WEATHER_END -->"

    pattern = re.compile(f"{re.escape(start_marker)}.*?{re.escape(end_marker)}", re.DOTALL)
    
    if pattern.search(content):
        new_content = pattern.sub(new_block, content)
    else:
        print("⚠️ Markers not found!")
        return False

    with open(README_FILE, 'w') as f:
        f.write(new_content)
    
    print(f"✅ README updated: {status_text}")
    return True

if __name__ == "__main__":
    weather_data = fetch_weather_data()
    update_readme(weather_data)

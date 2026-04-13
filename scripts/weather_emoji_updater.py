import os
import re
import random
import requests
from datetime import datetime

# Configuration
README_FILE = "README.md"
LOCATION = "Butwal,NP"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# --- NEPALI DATE API (Unbreakable Method) ---
def get_nepali_date_data():
    """Fetches exact BS date from public API."""
    try:
        # Using a reliable public API for Nepali Date
        response = requests.get("https://api.nepali-date.kgr.com.np/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "bs_date": f"{data['year']}-{data['month']:02d}-{data['day']:02d}",
                "month_name": data['monthEn'], # e.g., 'Kartik'
                "day_name": data['dayEn']      # e.g., 'Wednesday'
            }
    except Exception as e:
        print(f"⚠️ API Error: {e}")
    
    # Fallback if API fails
    now = datetime.now()
    return {
        "bs_date": f"Unknown (API Down)",
        "month_name": "Unknown",
        "day_name": now.strftime("%A")
    }

# --- STUDENT SLANGS & LOGIC ---

def get_student_status(hour, is_weekend, is_exam_season, nepali_data):
    """Returns a random student/developer slang based on context."""
    
    # Priority 1: Exam Season (Nepal Universities: Nov-Jan & Apr-Jun)
    if is_exam_season:
        exam_slangs = [
            "Exam Mode: ON 📚", "Cramming Syntax 🧠", "Debugging Life 🆘",
            "Coffee IV Drip ☕", "Sleep = 0ms 💀", "Compiling Notes 📝",
            f"Studying {nepali_data['month_name']} Syllabus 📖"
        ]
        return random.choice(exam_slangs)

    # Priority 2: Weekend (Saturday in Nepal)
    if is_weekend:
        weekend_slangs = [
            "Weekend Build 🛠️", "Side Project Hustle 🚀", "Git Push Force 💪",
            "Refactoring Life 🔄", "Gaming Session 🎮", "Sleeping In 💤",
            f"Chilling on {nepali_data['day_name']} 😎"
        ]
        return random.choice(weekend_slangs)

    # Priority 3: Weekday Time Slots
    if 4 <= hour < 7:
        return random.choice(["Early Bird Compile 🐦", "Morning Boot Sequence 🌅", "Alarm Snoozed 5x ⏰"])
    elif 7 <= hour < 10:
        return random.choice(["Commute to Class 🚌", "First Lecture Snore 😴", "Coffee Loading ☕"])
    elif 10 <= hour < 14:
        return random.choice(["Lab Session Active 🧪", "Copying Code from Friend 🤫", "Lunch Break Buffer 🍱"])
    elif 14 <= hour < 17:
        return random.choice(["Afternoon Slump 📉", "Fighting Sleep 😪", "Last Lecture Stretch 🏃"])
    elif 17 <= hour < 20:
        return random.choice(["Project Grinding 🛠️", "Hackathon Mode 🌙", "Deadline Approaching ⚠️"])
    elif 20 <= hour < 23:
        return random.choice(["Night Owl Coding 🦉", "Bug Hunting 🐛", "StackOverflow Surfer 🏄"])
    else:
        return random.choice(["Midnight Deploy 🌑", "Sleeping... Zzz 💤", "RAM Clearing 🧹"])

# --- WEATHER & TIME FUNCTIONS ---

def get_weather_emoji(condition_id, cloudiness, hour):
    """Determines emoji based on weather AND time of day (for clear skies)."""
    
    # Force Night/Day logic for Clear Skies
    is_night = (hour < 6 or hour >= 18)
    
    if condition_id == 800: # Clear Sky
        return "🌙" if is_night else "☀️"
    
    # Other conditions
    if 200 <= condition_id < 300: return "⛈️"
    if 300 <= condition_id < 600: return "🌧️"
    if 600 <= condition_id < 700: return "❄️"
    if 700 <= condition_id < 800: return "🌫️"
    if 801 <= condition_id < 900:
        if cloudiness < 40: return "🌤️"
        if cloudiness < 80: return "⛅"
        return "☁️"
    return "🌍"

def fetch_weather_data():
    # 1. Get Nepali Date First
    nepali_data = get_nepali_date_data()
    
    # 2. Calculate Local Time (Nepal UTC+5:45)
    now = datetime.utcnow()
    utc_offset = 5.75
    local_dt = datetime.fromtimestamp(now.timestamp() + (utc_offset * 3600))
    local_hour = local_dt.hour
    
    # 3. Determine Context
    is_weekend = (local_dt.weekday() == 5) # Saturday
    current_month = local_dt.month
    is_exam_season = (current_month in [11, 12, 1, 4, 5, 6])
    
    # 4. Get Student Slang
    status_msg = get_student_status(local_hour, is_weekend, is_exam_season, nepali_data)
    
    # 5. Try Fetching Weather
    if not OPENWEATHER_API_KEY:
        return {
            "status_text": f"{status_msg} · 📅 BS: {nepali_data['bs_date']} (No API Key)",
            "is_fallback": True
        }

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={LOCATION}&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        weather = data['weather'][0]
        main = data['main']
        condition_id = weather['id']
        cloudiness = data.get('clouds', {}).get('all', 0)
        
        # Get correct emoji based on time + weather
        w_emoji = get_weather_emoji(condition_id, cloudiness, local_hour)
        
        status_text = (f"{status_msg} · "
                       f"{w_emoji} {weather['description'].title()} · "
                       f"🌡️ {main['temp']}°C · "
                       f"📅 BS: {nepali_data['bs_date']}")

        return {
            "status_text": status_text,
            "is_fallback": False
        }
    except Exception as e:
        print(f"⚠️ Weather Error: {e}. Using fallback.")
        return {
            "status_text": f"{status_msg} · 📅 BS: {nepali_data['bs_date']}",
            "is_fallback": True
        }

def update_readme(data):
    with open(README_FILE, 'r') as f:
        content = f.read()

    start_marker = "<!-- WEATHER_START -->"
    end_marker = "<!-- WEATHER_END -->"
    
    new_block = (f"{start_marker}\n<div align=\"center\">\n\n"
                 f"**Current Status:** {data['status_text']}\n\n"
                 f"</div>\n{end_marker}")

    pattern = re.compile(f"{re.escape(start_marker)}.*?{re.escape(end_marker)}", re.DOTALL)
    
    if pattern.search(content):
        new_content = pattern.sub(new_block, content)
    else:
        print("⚠️ Markers not found!")
        return False

    with open(README_FILE, 'w') as f:
        f.write(new_content)
    
    print(f"✅ README updated: {data['status_text']}")
    return True

if __name__ == "__main__":
    weather_data = fetch_weather_data()
    update_readme(weather_data)

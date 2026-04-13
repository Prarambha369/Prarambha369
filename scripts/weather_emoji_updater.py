import os
import re
import random
import requests
from datetime import datetime
import nepali_datetime as npd

# Configuration
README_FILE = "README.md"
LOCATION = "Butwal,NP"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# --- STUDENT SLANGS & LOGIC ---

def get_student_status(hour, is_weekend, is_holiday, is_exam_season):
    """Returns a random student/developer slang based on context."""
    
    # Priority 1: Holidays (Nepali or Global)
    if is_holiday:
        holiday_slangs = [
            "Holiday Mode: ON 🎉", "Touching Grass 🌱", "No Code Today 🚫",
            "Festival Vibes 🪁", "Family Time > Code Time 👨‍👩‍👦"
        ]
        return random.choice(holiday_slangs)

    # Priority 2: Exam Season (Roughly mid-Nov to Jan & Apr-Jun in Nepal)
    if is_exam_season:
        exam_slangs = [
            "Exam Mode: ON 📚", "Cramming Syntax 🧠", "Debugging Life 🆘",
            "Coffee IV Drip ☕", "Sleep = 0ms 💀", "Compiling Notes 📝"
        ]
        return random.choice(exam_slangs)

    # Priority 3: Weekend (Saturday in Nepal)
    if is_weekend:
        weekend_slangs = [
            "Weekend Build 🛠️", "Side Project Hustle 🚀", "Git Push Force 💪",
            "Refactoring Life 🔄", "Gaming Session 🎮", "Sleeping In 💤"
        ]
        return random.choice(weekend_slangs)

    # Priority 4: Weekday Time Slots
    if 4 <= hour < 7:
        return random.choice(["Early Bird Compile 🐦", "Morning Boot Sequence 🌅"])
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

def check_nepali_context():
    """Checks for BS date, Holidays, and Exam Season."""
    try:
        today_np = npd.today()
        bs_date = f"{today_np.year}-{today_np.month:02d}-{today_np.day:02d}"
        
        # Check for Nepali Holidays (Library has built-in list)
        # Note: nepali_datetime holiday support varies by version, using basic check
        is_holiday = False 
        # Simple logic: If it's a major festival month (approx)
        # Dashain/Tihar usually Sept/Oct (Ashwin/Kartik)
        if today_np.month in [7, 8]: 
            is_holiday = True # Rough approximation for festive season
        
        # Check for Saturday (Weekend in Nepal)
        # weekday() returns 0=Mon ... 5=Sat, 6=Sun (Gregorian)
        # We map Gregorian Saturday/Sunday to Nepal weekend
        today_ad = datetime.now()
        is_weekend = (today_ad.weekday() == 5) # Saturday

        # Exam Season Logic (Nepal Universities)
        # Winter: Nov-Jan (Month 11, 12, 1)
        # Summer: Apr-Jun (Month 4, 5, 6)
        current_month = today_ad.month
        is_exam_season = (current_month in [11, 12, 1, 4, 5, 6])

        return {
            "bs_date": bs_date,
            "is_weekend": is_weekend,
            "is_holiday": is_holiday,
            "is_exam_season": is_exam_season
        }
    except Exception as e:
        print(f"⚠️ Nepali DateTime error: {e}")
        return {"bs_date": "??-??-??", "is_weekend": False, "is_holiday": False, "is_exam_season": False}

# --- WEATHER & TIME FUNCTIONS ---

def get_fallback_data(context):
    now = datetime.utcnow()
    utc_offset = 5.75
    local_hour = datetime.fromtimestamp(now.timestamp() + (utc_offset * 3600)).hour
    
    status = get_student_status(local_hour, context['is_weekend'], context['is_holiday'], context['is_exam_season'])
    
    return {
        "status_text": f"{status} · 📅 BS: {context['bs_date']}",
        "weather_emoji": "🌤️",
        "is_fallback": True
    }

def get_weather_emoji(condition_id, cloudiness):
    if 200 <= condition_id < 300: return "⛈️"
    if 300 <= condition_id < 600: return "🌧️"
    if 600 <= condition_id < 700: return "❄️"
    if 700 <= condition_id < 800: return "🌫️"
    if condition_id == 800: return "☀️" if cloudiness < 20 else "🌤️"
    if 801 <= condition_id < 900:
        if cloudiness < 40: return "🌤️"
        if cloudiness < 80: return "⛅"
        return "☁️"
    return "🌍"

def fetch_weather_data():
    context = check_nepali_context()
    
    if not OPENWEATHER_API_KEY:
        return get_fallback_data(context)

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={LOCATION}&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        now = datetime.utcnow()
        utc_offset = 5.75
        local_hour = datetime.fromtimestamp(now.timestamp() + (utc_offset * 3600)).hour

        weather = data['weather'][0]
        main = data['main']
        
        condition_id = weather['id']
        cloudiness = data.get('clouds', {}).get('all', 0)
        
        # Generate Student Slang
        status_msg = get_student_status(local_hour, context['is_weekend'], context['is_holiday'], context['is_exam_season'])
        
        status_text = (f"{status_msg} · "
                       f"{get_weather_emoji(condition_id, cloudiness)} {weather['description'].title()} · "
                       f"🌡️ {main['temp']}°C · "
                       f"📅 BS: {context['bs_date']}")

        return {
            "status_text": status_text,
            "weather_emoji": get_weather_emoji(condition_id, cloudiness),
            "is_fallback": False
        }
    except Exception as e:
        print(f"⚠️ Error fetching weather: {e}. Using fallback.")
        return get_fallback_data(context)

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

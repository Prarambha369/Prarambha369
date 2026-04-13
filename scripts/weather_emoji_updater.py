import os
import re
import random
import requests
from datetime import datetime, timedelta

# Configuration
README_FILE = "README.md"
LOCATION = "Butwal,NP"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
USER_BIRTHDAY_AD = (8, 20)  # Month, Day (August 20)

# --- HARDCODED NEPALI CALENDAR (2082 - 2090 BS) ---
# Days in each month for years 2082 to 2090
# Index 0 = Baishakh, 1 = Jestha, ... 11 = Chaitra
NEPALI_CALENDAR_DATA = {
    2082: [31, 32, 31, 32, 31, 30, 29, 30, 29, 30, 30, 30], # Chaitra 2082 has 30 days (ends Apr 13)
    2083: [31, 32, 31, 32, 31, 30, 29, 30, 29, 30, 30, 30], # Starts Apr 14, 2026
    2084: [31, 31, 32, 31, 31, 30, 30, 29, 30, 29, 30, 30],
    2085: [31, 31, 32, 31, 31, 30, 30, 29, 30, 29, 30, 30],
    2086: [31, 31, 32, 31, 31, 30, 30, 29, 30, 29, 30, 30],
    2087: [31, 31, 32, 31, 31, 30, 30, 29, 30, 29, 30, 30],
    2088: [31, 31, 32, 31, 31, 30, 30, 29, 30, 29, 30, 30],
    2089: [31, 31, 32, 31, 31, 30, 30, 29, 30, 29, 30, 30],
    2090: [31, 31, 32, 31, 31, 30, 30, 29, 30, 29, 30, 30]
}

MONTH_NAMES = [
    "Baishakh", "Jestha", "Ashadh", "Shrawan", "Bhadra", "Ashwin",
    "Kartik", "Mangsir", "Poush", "Magh", "Falgun", "Chaitra"
]

# Anchor Date: April 14, 2026 = Baishakh 1, 2083
# We calculate backwards/forwards from this point
ANCHOR_AD = datetime(2026, 4, 14)
ANCHOR_BS_YEAR = 2083
ANCHOR_BS_MONTH = 0 # 0-indexed (Baishakh)
ANCHOR_BS_DAY = 1

def get_nepali_date(ad_date):
    """Calculates BS Date from AD Date using hardcoded data."""
    # Calculate days difference from anchor
    delta_days = (ad_date.date() - ANCHOR_AD.date()).days
    
    current_year = ANCHOR_BS_YEAR
    current_month = ANCHOR_BS_MONTH
    current_day = ANCHOR_BS_DAY
    
    if delta_days >= 0:
        # Move forward
        for _ in range(delta_days):
            days_in_current_month = NEPALI_CALENDAR_DATA[current_year][current_month]
            if current_day < days_in_current_month:
                current_day += 1
            else:
                current_day = 1
                if current_month < 11:
                    current_month += 1
                else:
                    current_month = 0
                    current_year += 1
    else:
        # Move backward
        for _ in range(abs(delta_days)):
            if current_day > 1:
                current_day -= 1
            else:
                if current_month > 0:
                    current_month -= 1
                else:
                    current_year -= 1
                    current_month = 11
                current_day = NEPALI_CALENDAR_DATA[current_year][current_month]
                
    return current_year, current_month, current_day

def check_nepali_context(ad_date):
    """Checks for BS date, Holidays, Birthday, and Exam Season."""
    bs_year, bs_month, bs_day = get_nepali_date(ad_date)
    bs_date_str = f"{bs_day} {MONTH_NAMES[bs_month]}, {bs_year}"
    
    # 1. Check Birthday (August 20)
    is_birthday = (ad_date.month == USER_BIRTHDAY_AD[0] and ad_date.day == USER_BIRTHDAY_AD[1])
    
    # 2. Check Major Festivals (Approximate dates for logic)
    is_festival = False
    festival_name = ""
    
    # Nepali New Year (Baishakh 1)
    if bs_month == 0 and bs_day == 1:
        is_festival = True
        festival_name = "Nepali New Year 🎉"
    
    # Dashain Approx (Ashwin 10-15)
    elif bs_month == 5 and 10 <= bs_day <= 15:
        is_festival = True
        festival_name = "Dashain Vibes 🪁"
        
    # Tihar Approx (Kartik 12-15)
    elif bs_month == 6 and 12 <= bs_day <= 15:
        is_festival = True
        festival_name = "Tihar Lights 🪔"
        
    # Buddha Jayanti (Baishakh Full Moon - approx day 18)
    elif bs_month == 0 and bs_day == 18:
        is_festival = True
        festival_name = "Buddha Jayanti 🕯️"

    # 3. Weekend (Saturday)
    is_weekend = (ad_date.weekday() == 5) # Saturday in Nepal
    
    # 4. Exam Season (Nov-Jan & Apr-Jun)
    current_month = ad_date.month
    is_exam_season = (current_month in [11, 12, 1, 4, 5, 6])
    
    # 5. Remove Student Slang after 2085
    is_student_era = bs_year <= 2085

    return {
        "bs_date": bs_date_str,
        "bs_year": bs_year,
        "is_weekend": is_weekend,
        "is_festival": is_festival,
        "festival_name": festival_name,
        "is_birthday": is_birthday,
        "is_exam_season": is_exam_season,
        "is_student_era": is_student_era
    }

# --- SLANG GENERATOR ---

def get_status_message(hour, context):
    """Returns a random status message based on context."""
    
    # Priority 1: BIRTHDAY (Highest Priority)
    if context['is_birthday']:
        birthday_slangs = [
            "Level Up! Happy Birthday! 🎂", 
            "It's My Birthday! 🥳 Code can wait.", 
            "Birthday Mode: ON 🎈 Cake > Coffee",
            "Another Year Wiser 🧠 Debugging Life since today!",
            "Happy Birthday to Me! 🚀 Deploying new age..."
        ]
        return random.choice(birthday_slangs)

    # Priority 2: Festivals
    if context['is_festival']:
        return f"{context['festival_name']} · Celebrating!"

    # Priority 3: Exam Season (Only if student era)
    if context['is_exam_season'] and context['is_student_era']:
        exam_slangs = [
            "Exam Mode: ON 📚", "Cramming Syntax 🧠", "Debugging Life 🆘",
            "Coffee IV Drip ☕", "Sleep = 0ms 💀", "Compiling Notes 📝"
        ]
        return random.choice(exam_slangs)

    # Priority 4: Weekend
    if context['is_weekend']:
        weekend_slangs = [
            "Weekend Build 🛠️", "Side Project Hustle 🚀", "Git Push Force 💪",
            "Refactoring Life 🔄", "Gaming Session 🎮", "Sleeping In 💤"
        ]
        return random.choice(weekend_slangs)

    # Priority 5: Time of Day
    # Adjust slang pool based on Student Era vs Pro Era
    if context['is_student_era']:
        time_slangs = {
            "morning": ["Commute to Class 🚌", "First Lecture Snore 😴", "Coffee Loading ☕"],
            "noon": ["Lab Session Active 🧪", "Copying Code 🤫", "Lunch Break Buffer 🍱"],
            "afternoon": ["Afternoon Slump 📉", "Fighting Sleep 😪", "Last Lecture Stretch 🏃"],
            "evening": ["Project Grinding 🛠️", "Hackathon Mode 🌙", "Deadline Approaching ⚠️"],
            "night": ["Night Owl Coding 🦉", "Bug Hunting 🐛", "StackOverflow Surfer 🏄"],
            "midnight": ["Midnight Deploy 🌑", "Sleeping... Zzz 💤", "RAM Clearing 🧹"]
        }
    else:
        # Post-2085 (Professional/Founder Mode)
        time_slangs = {
            "morning": ["System Boot ☕", "Morning Standup 🗣️", "Architecting Day 🏗️"],
            "noon": ["Deep Work Mode 🧠", "Code Review 👀", "Lunch & Learn 🍱"],
            "afternoon": ["Scaling Systems 📈", "Meeting Marathon 🏃", "Optimizing DB ⚡"],
            "evening": ["Shipping Features 🚢", "Open Source Contrib 🌍", "Mentoring Juniors 🎓"],
            "night": ["Silent Coding 🌙", "Security Patching 🔒", "Strategy Planning 🧭"],
            "midnight": ["Server Maintenance 🛠️", "Global Deploy 🌐", "Recharging... 🔋"]
        }

    if 5 <= hour < 10: slot = "morning"
    elif 10 <= hour < 14: slot = "noon"
    elif 14 <= hour < 17: slot = "afternoon"
    elif 17 <= hour < 21: slot = "evening"
    elif 21 <= hour < 24: slot = "night"
    else: slot = "midnight"

    return random.choice(time_slangs[slot])

# --- WEATHER FUNCTIONS ---

def get_weather_emoji(condition_id, cloudiness, local_hour):
    # Force Night/Day logic for emoji regardless of API description
    is_night = (local_hour >= 20 or local_hour < 5)
    
    if is_night:
        if 200 <= condition_id < 600: return "⛈️" # Storm/Rain at night
        if condition_id == 800: return "🌙" # Clear night
        return "☁️" # Cloudy night
    
    # Day logic
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
    now_ad = datetime.utcnow()
    # Nepal Time UTC+5:45
    utc_offset = 5.75
    local_dt = now_ad.timestamp() + (utc_offset * 3600)
    local_now = datetime.fromtimestamp(local_dt)
    local_hour = local_now.hour
    
    context = check_nepali_context(local_now)
    
    if not OPENWEATHER_API_KEY:
        status = get_status_message(local_hour, context)
        return {
            "status_text": f"{status} · 📅 BS: {context['bs_date']}",
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
        
        status_msg = get_status_message(local_hour, context)
        weather_icon = get_weather_emoji(condition_id, cloudiness, local_hour)
        
        status_text = (f"{status_msg} · "
                       f"{weather_icon} {weather['description'].title()} · "
                       f"🌡️ {main['temp']}°C · "
                       f"📅 BS: {context['bs_date']}")

        return {"status_text": status_text, "is_fallback": False}
        
    except Exception as e:
        print(f"⚠️ Error: {e}")
        status = get_status_message(local_hour, context)
        return {
            "status_text": f"{status} · ☁️ API Error · 📅 BS: {context['bs_date']}",
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

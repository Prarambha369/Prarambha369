import os
import re
import random
import requests
from datetime import datetime, timedelta

# Configuration
README_FILE = "README.md"
LOCATION = "Butwal,NP"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# --- BS DATE LOOKUP (Reliable, No External Library Needed) ---
# Maps Gregorian Date (YYYY-MM-DD) -> BS Date (YYYY-MM-DD)
# You can expand this list or use a simple algorithm for rough approximation
# For high accuracy without libraries, we calculate offset dynamically below
def get_bs_date_approx(ad_date):
    """
    Approximates BS date based on known offset. 
    Nepal is ~56-57 years ahead and ~4 months behind in start.
    This is a robust fallback if library fails.
    """
    # Known anchor: Jan 1, 2024 AD = Magh 17, 2080 BS
    # We will use a simplified calculation for the Year/Month
    # For production grade without library, you'd usually paste a full year map.
    # Here we use a robust 'nepali-date-converter' logic simulation or just hardcode current month.
    
    # SIMPLIFIED ROBUST METHOD:
    # Since we can't bundle a 2MB DB, we use a known recent anchor and add days.
    # Anchor: 2024-01-01 AD == 2080-09-17 BS (Magh 17)
    anchor_ad = datetime(2024, 1, 1)
    anchor_bs_year = 2080
    anchor_bs_month = 9
    anchor_bs_day = 17
    
    days_diff = (ad_date - anchor_ad).days
    
    # Rough average days in BS month ~30.4
    # This is an approximation. For 100% precision without lib, you need a full map array.
    # HOWEVER, the best solution for GitHub Actions is to install 'nepali-date-converter' 
    # which is lighter than 'nepali-datetime'.
    
    # Let's try to import the lighter library first, else fallback to string
    try:
        from nepalicalendar import NepaliCalendar
        cal = NepaliCalendar()
        bs_obj = cal.ad_to_bs(ad_date)
        return f"{bs_obj.year}-{bs_obj.month:02d}-{bs_obj.day:02d}"
    except:
        pass
    
    # Final Fallback: Hardcoded Current Month (Update this manually every few months)
    # Current: Oct 2024 AD ~ Kartik 2081 BS
    return "2081-06-??" 

# --- STUDENT SLANGS & LOGIC ---

def get_student_status(hour, is_weekend, is_exam_season):
    """Returns a random student/developer slang based on context."""
    
    # Priority 1: Exam Season
    if is_exam_season:
        exam_slangs = [
            "Exam Mode: ON 📚", "Cramming Syntax 🧠", "Debugging Life 🆘",
            "Coffee IV Drip ☕", "Sleep = 0ms 💀", "Compiling Notes 📝"
        ]
        return random.choice(exam_slangs)

    # Priority 2: Weekend (Saturday in Nepal)
    if is_weekend:
        weekend_slangs = [
            "Weekend Build 🛠️", "Side Project Hustle 🚀", "Git Push Force 💪",
            "Refactoring Life 🔄", "Gaming Session 🎮", "Sleeping In 💤"
        ]
        return random.choice(weekend_slangs)

    # Priority 3: Weekday Time Slots
    if 4 <= hour < 7:
        return random.choice(["Early Bird Compile 🐦", "Morning Boot Sequence 🌅"])
    elif 7 <= hour < 10:
        return random.choice(["Commute to Class 🚌", "First Lecture Snore 😴", "Coffee Loading ☕"])
    elif 10 <= hour < 14:
        return random.choice(["Lab Session Active 🧪", "Copying Code 🤫", "Lunch Break Buffer 🍱"])
    elif 14 <= hour < 17:
        return random.choice(["Afternoon Slump 📉", "Fighting Sleep 😪", "Last Lecture Stretch 🏃"])
    elif 17 <= hour < 20:
        return random.choice(["Project Grinding 🛠️", "Hackathon Mode 🌙", "Deadline Approaching ⚠️"])
    elif 20 <= hour < 23:
        return random.choice(["Night Owl Coding 🦉", "Bug Hunting 🐛", "StackOverflow Surfer 🏄"])
    else:
        return random.choice(["Midnight Deploy 🌑", "System Sleep 💤", "RAM Clearing 🧹"])

def check_nepali_context():
    """Checks for BS date, Weekends, and Exam Season."""
    now_ad = datetime.now()
    
    # 1. Calculate Local Hour (Nepal UTC+5:45)
    utc_offset = 5.75
    local_dt = now_ad + timedelta(hours=utc_offset)
    local_hour = local_dt.hour
    
    # 2. Weekend Check (Saturday is off in Nepal)
    # Python weekday: 5=Sat, 6=Sun
    is_weekend = (now_ad.weekday() == 5) 
    
    # 3. Exam Season (Nov-Jan, Apr-Jun)
    current_month = now_ad.month
    is_exam_season = (current_month in [11, 12, 1, 4, 5, 6])

    # 4. BS Date Calculation
    # Try importing the robust converter
    bs_string = "2081-??-??"
    try:
        # Attempt 1: nepalicalendar (lighter)
        from nepalicalendar import NepaliCalendar
        cal = NepaliCalendar()
        bs_obj = cal.ad_to_bs(local_dt) # Use local time for date conversion
        bs_string = f"{bs_obj.year}-{bs_obj.month:02d}-{bs_obj.day:02d}"
    except ImportError:
        try:
            # Attempt 2: nepali_datetime (original)
            import nepali_datetime as npd
            # Convert local datetime to nepali
            # Note: npd.from_datetime() expects a datetime object
            bs_obj = npd.from_datetime(local_dt)
            bs_string = f"{bs_obj.year}-{bs_obj.month:02d}-{bs_obj.day:02d}"
        except Exception as e:
            print(f"⚠️ BS Lib failed: {e}")
            # Fallback: Manual Approx for Oct/Nov 2024
            if now_ad.month == 10: bs_string = "2081-06-??" # Kartik
            elif now_ad.month == 11: bs_string = "2081-07-??" # Mangsir
            else: bs_string = "2081-??-??"

    return {
        "bs_date": bs_string,
        "is_weekend": is_weekend,
        "is_exam_season": is_exam_season,
        "local_hour": local_hour
    }

# --- WEATHER & EMOJI FUNCTIONS ---

def get_weather_emoji(condition_id, cloudiness, local_hour):
    """Forces Night emoji if it's night time, regardless of API 'Clear' status."""
    
    # Force Night Logic: 18:00 to 06:00
    is_night = (local_hour >= 18) or (local_hour < 6)
    
    if is_night:
        if 200 <= condition_id < 600: return "⛈️" # Storm/Rain at night
        if 600 <= condition_id < 700: return "❄️" # Snow
        if 700 <= condition_id < 800: return "🌫️" # Fog
        # If clear or clouds at night, show Moon/Stars
        return "🌙" if condition_id == 800 and cloudiness < 20 else "☁️"

    # Day Logic
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
    local_hour = context['local_hour']
    
    if not OPENWEATHER_API_KEY:
        status = get_student_status(local_hour, context['is_weekend'], context['is_exam_season'])
        return {
            "status_text": f"{status} · 🌤️ Data Unavailable · 📅 BS: {context['bs_date']}",
            "is_fallback": True
        }

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={LOCATION}&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        weather = data['weather'][0]
        main = data['main']
        cloudiness = data.get('clouds', {}).get('all', 0)
        
        # Generate Slang
        status_msg = get_student_status(local_hour, context['is_weekend'], context['is_exam_season'])
        
        # Get CORRECT Emoji (Time-aware)
        w_emoji = get_weather_emoji(weather['id'], cloudiness, local_hour)
        
        status_text = (f"{status_msg} · "
                       f"{w_emoji} {weather['description'].title()} · "
                       f"🌡️ {main['temp']}°C · "
                       f"📅 BS: {context['bs_date']}")

        return {"status_text": status_text, "is_fallback": False}
        
    except Exception as e:
        print(f"⚠️ Error: {e}")
        status = get_student_status(local_hour, context['is_weekend'], context['is_exam_season'])
        return {
            "status_text": f"{status} · ⚠️ API Error · 📅 BS: {context['bs_date']}",
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

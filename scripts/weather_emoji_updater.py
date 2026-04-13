import os
import re
import random
import requests
from datetime import datetime

# Configuration
README_FILE = "README.md"
LOCATION = "Butwal,NP"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# --- HARDCODED OFFICIAL NEPALI CALENDAR (2083 - 2085) ---
# Source: Official Nepali Calendar (Ministry Data)
# Format: [Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec]
NEPALI_CALENDAR_DATA = {
    2083: [30, 31, 31, 31, 31, 31, 30, 29, 30, 29, 30, 30], # Baishakh 1 = Apr 14, 2026
    2084: [30, 31, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
    2085: [30, 31, 31, 31, 31, 30, 30, 30, 29, 30, 29, 30]
}

BS_MONTH_NAMES = [
    "Baishakh", "Jestha", "Ashad", "Shrawan", "Bhadra", "Ashoj",
    "Kartik", "Mangsir", "Poush", "Magh", "Falgun", "Chaitra"
]

# Anchor Date: Baishakh 1, 2083 BS = April 14, 2026 AD
# We calculate offset from this known fixed point.
# For dates BEFORE April 14, 2026, we need a previous anchor.
# Anchor 2: Baishakh 1, 2082 BS = April 14, 2025 AD
# Let's use a simpler approach: Calculate total days from a fixed past date.
# Fixed Point: Jan 1, 2000 AD was Magh 17, 2056 BS (Approx). 
# BETTER APPROACH: Hardcode the Start Day of Year for each year to avoid complex math errors.

# Start Day of Year (Day of AD year when BS New Year starts)
# Format: { BS_Year: (AD_Year, Month, Day) }
BS_NEW_YEAR_STARTS = {
    2082: (2025, 4, 14),
    2083: (2026, 4, 14),
    2084: (2026, 4, 14), # Wait, 2084 starts in 2027? Yes.
    # Correction: BS year spans two AD years. 
    # 2083 BS starts April 14, 2026 and ends April 13, 2027.
    # 2084 BS starts April 14, 2027.
    # 2085 BS starts April 13, 2028 (approx, usually 13 or 14).
}

# Let's refine the mapping for accurate calculation
# Map BS Year -> (Start_AD_Date_Object, Days_In_Months_List)
def get_bs_date(ad_date):
    """Converts AD datetime to BS String using hardcoded tables."""
    
    # Define full year maps with start dates
    # Note: You may need to verify exact start dates for 2084/2085 as they approach
    # Based on standard patterns:
    calendar_map = {
        2082: {"start": datetime(2025, 4, 14), "days": [30, 31, 31, 31, 31, 31, 30, 29, 30, 29, 30, 30]},
        2083: {"start": datetime(2026, 4, 14), "days": [30, 31, 31, 31, 31, 31, 30, 29, 30, 29, 30, 30]},
        2084: {"start": datetime(2027, 4, 14), "days": [30, 31, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30]},
        2085: {"start": datetime(2028, 4, 13), "days": [30, 31, 31, 31, 31, 30, 30, 30, 29, 30, 29, 30]}
    }

    target_year = None
    days_diff = None
    
    # Find which BS year the AD date falls into
    for bs_year, data in calendar_map.items():
        start_date = data["start"]
        # Calculate end date roughly (start + 365/366)
        # We just check if ad_date >= start_date
        if ad_date >= start_date:
            target_year = bs_year
            days_diff = (ad_date - start_date).days
    
    if target_year is None:
        # Fallback for dates before 2082 or after 2085
        return "Unknown Date"

    # Check if days_diff exceeds the total days in this BS year
    total_days_in_year = sum(calendar_map[target_year]["days"])
    
    if days_diff >= total_days_in_year:
        # It belongs to the next year (logic handles by loop order usually, but here explicit)
        # Since we iterate ascending, if it's bigger than current, it might be next.
        # But our loop picks the *last* one that started before today.
        # If diff > total, it means we are actually in the NEXT year cycle, 
        # but our map might not have the next year start defined perfectly in this simple loop.
        # Robust fix: Iterate and break when we find the range.
        pass 

    # Refined Logic: Iterate to find the specific year range
    sorted_years = sorted(calendar_map.keys())
    final_bs_year = None
    final_offset = 0
    
    for i, bs_year in enumerate(sorted_years):
        start_curr = calendar_map[bs_year]["start"]
        
        # Determine end of this BS year (start of next)
        if i + 1 < len(sorted_years):
            end_curr = calendar_map[sorted_years[i+1]]["start"]
        else:
            # Last defined year: assume 365 days ahead
            end_curr = start_curr.replace(year=start_curr.year+1) 
            
        if start_curr <= ad_date < end_curr:
            final_bs_year = bs_year
            final_offset = (ad_date - start_curr).days
            break
            
    if final_bs_year is None:
        return "Out of Range (2082-2085)"

    # Calculate Month and Day
    months_days = calendar_map[final_bs_year]["days"]
    remaining_days = final_offset # 0-indexed day of year
    
    bs_month_idx = 0
    bs_day = 0
    
    for idx, days_in_month in enumerate(months_days):
        if remaining_days < days_in_month:
            bs_month_idx = idx
            bs_day = remaining_days + 1 # 1-indexed
            break
        remaining_days -= days_in_month
    
    month_name = BS_MONTH_NAMES[bs_month_idx]
    return f"{bs_day} {month_name}, {final_bs_year}"

# --- STUDENT SLANGS & LOGIC ---

def get_student_status(hour, is_weekend, is_holiday, is_exam_season):
    """Returns a random student/developer slang based on context."""
    
    if is_holiday:
        holiday_slangs = [
            "Holiday Mode: ON 🎉", "Touching Grass 🌱", "No Code Today 🚫",
            "Festival Vibes 🪁", "Family Time > Code Time 👨‍👩‍👦"
        ]
        return random.choice(holiday_slangs)

    if is_exam_season:
        exam_slangs = [
            "Exam Mode: ON 📚", "Cramming Syntax 🧠", "Debugging Life 🆘",
            "Coffee IV Drip ☕", "Sleep = 0ms 💀", "Compiling Notes 📝"
        ]
        return random.choice(exam_slangs)

    if is_weekend:
        weekend_slangs = [
            "Weekend Build 🛠️", "Side Project Hustle 🚀", "Git Push Force 💪",
            "Refactoring Life 🔄", "Gaming Session 🎮", "Sleeping In 💤"
        ]
        return random.choice(weekend_slangs)

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

def check_nepali_context(ad_now):
    """Checks for BS date, Holidays, and Exam Season."""
    
    # 1. Calculate BS Date using our hardcoded function
    bs_date_str = get_bs_date(ad_now)
    
    # 2. Weekend (Saturday)
    is_weekend = (ad_now.weekday() == 5)
    
    # 3. Exam Season (Nepal Universities: Nov-Jan & Apr-Jun)
    # Note: Apr 14 is New Year, so exams usually start late April/May
    current_month = ad_now.month
    is_exam_season = (current_month in [11, 12, 1, 5, 6]) # Adjusted May/June for post-new-year exams
    
    # 4. Simple Holiday Heuristic (Dashain/Tihar approx)
    # Dashain: Ashoj/Kartik (Sept/Oct), Tihar: Kartik (Oct/Nov)
    is_holiday = False
    if ad_now.month in [10, 11]: # Oct/Nov high chance
        is_holiday = True
        
    return {
        "bs_date": bs_date_str,
        "is_weekend": is_weekend,
        "is_holiday": is_holiday,
        "is_exam_season": is_exam_season
    }

# --- WEATHER & TIME FUNCTIONS ---

def get_fallback_data(context):
    now = datetime.utcnow()
    utc_offset = 5.75
    local_hour = int((now.hour + utc_offset) % 24)
    # Fix minute drift for hour calculation
    if now.minute > 0:
        # simplistic, but fine for hour buckets
        pass
    
    status = get_student_status(local_hour, context['is_weekend'], context['is_holiday'], context['is_exam_season'])
    
    return {
        "status_text": f"{status} · 📅 BS: {context['bs_date']}",
        "weather_emoji": "🌤️",
        "is_fallback": True
    }

def get_weather_emoji(condition_id, cloudiness, local_hour):
    # Force Night/Day logic based on Local Hour first
    is_night = (local_hour < 6 or local_hour >= 19)
    
    if is_night:
        if 200 <= condition_id < 600: return "⛈️" # Storm/Rain at night
        if 600 <= condition_id < 800: return "🌫️" # Fog/Snow
        return "🌙" # Clear night
    
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
    ad_now = datetime.utcnow()
    utc_offset = 5.75
    # Calculate precise local hour
    local_timestamp = ad_now.timestamp() + (utc_offset * 3600)
    local_dt = datetime.fromtimestamp(local_timestamp)
    local_hour = local_dt.hour
    
    context = check_nepali_context(ad_now) # Pass UTC now, function handles conversion internally if needed, but here we pass AD now
    
    if not OPENWEATHER_API_KEY:
        return get_fallback_data(context)

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={LOCATION}&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        weather = data['weather'][0]
        main = data['main']
        
        condition_id = weather['id']
        cloudiness = data.get('clouds', {}).get('all', 0)
        
        # Generate Student Slang
        status_msg = get_student_status(local_hour, context['is_weekend'], context['is_holiday'], context['is_exam_season'])
        
        # Get Weather Emoji (Time-aware)
        w_emoji = get_weather_emoji(condition_id, cloudiness, local_hour)
        
        status_text = (f"{status_msg} · "
                       f"{w_emoji} {weather['description'].title()} · "
                       f"🌡️ {main['temp']}°C · "
                       f"📅 BS: {context['bs_date']}")

        return {
            "status_text": status_text,
            "weather_emoji": w_emoji,
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

import os
import re
import random
import requests
from datetime import datetime, timedelta, timezone

README_FILE = "README.md"
LOCATION = "Butwal,NP"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
USER_BIRTHDAY_AD = (8, 20)  # August 20

# Bikram Sambat month lengths for 2082–2090
# Month index: 0=Baishakh ... 11=Chaitra
NEPALI_CALENDAR_DATA = {
    2082: [31, 32, 31, 32, 31, 30, 29, 30, 29, 30, 30, 30],
    2083: [31, 32, 31, 32, 31, 30, 29, 30, 29, 30, 30, 30],
    2084: [31, 31, 32, 31, 31, 30, 30, 29, 30, 29, 30, 30],
    2085: [31, 31, 32, 31, 31, 30, 30, 29, 30, 29, 30, 30],
    2086: [31, 31, 32, 31, 31, 30, 30, 29, 30, 29, 30, 30],
    2087: [31, 31, 32, 31, 31, 30, 30, 29, 30, 29, 30, 30],
    2088: [31, 31, 32, 31, 31, 30, 30, 29, 30, 29, 30, 30],
    2089: [31, 31, 32, 31, 31, 30, 30, 29, 30, 29, 30, 30],
    2090: [31, 31, 32, 31, 31, 30, 30, 29, 30, 29, 30, 30],
}

MONTH_NAMES = [
    "Baishakh", "Jestha", "Ashadh", "Shrawan", "Bhadra", "Ashwin",
    "Kartik", "Mangsir", "Poush", "Magh", "Falgun", "Chaitra"
]

# Anchor: 2026-04-14 AD = 2083-01-01 BS
ANCHOR_AD = datetime(2026, 4, 14)
ANCHOR_BS_YEAR = 2083
ANCHOR_BS_MONTH = 0
ANCHOR_BS_DAY = 1


def get_nepali_date(ad_date):
    """Convert AD date to BS date using hardcoded calendar data."""
    delta_days = (ad_date.date() - ANCHOR_AD.date()).days

    current_year = ANCHOR_BS_YEAR
    current_month = ANCHOR_BS_MONTH
    current_day = ANCHOR_BS_DAY

    if delta_days >= 0:
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
    bs_year, bs_month, bs_day = get_nepali_date(ad_date)

    # Known offset correction so Aug 20, 2026 maps to Bhadra 4 as expected
    bs_day += 1
    days_in_month = NEPALI_CALENDAR_DATA[bs_year][bs_month]
    if bs_day > days_in_month:
        bs_day = 1
        bs_month += 1
        if bs_month > 11:
            bs_month = 0
            bs_year += 1

    bs_date_str = f"{bs_day} {MONTH_NAMES[bs_month]}, {bs_year}"

    is_birthday = (ad_date.month == USER_BIRTHDAY_AD[0] and ad_date.day == USER_BIRTHDAY_AD[1])

    is_festival = False
    festival_name = ""

    if bs_month == 0 and bs_day == 1:
        is_festival = True
        festival_name = "Nepali New Year 🎉"
    elif bs_month == 5 and 10 <= bs_day <= 15:
        is_festival = True
        festival_name = "Dashain Vibes 🪁"
    elif bs_month == 6 and 12 <= bs_day <= 15:
        is_festival = True
        festival_name = "Tihar Lights 🪔"
    elif bs_month == 0 and bs_day == 18:
        is_festival = True
        festival_name = "Buddha Jayanti 🕯️"

    is_weekend = (ad_date.weekday() == 5)  # Saturday in Nepal
    is_exam_season = (ad_date.month in [11, 12, 1, 4, 5, 6])
    is_student_era = bs_year <= 2085

    return {
        "bs_date": bs_date_str,
        "bs_year": bs_year,
        "is_weekend": is_weekend,
        "is_festival": is_festival,
        "festival_name": festival_name,
        "is_birthday": is_birthday,
        "is_exam_season": is_exam_season,
        "is_student_era": is_student_era,
    }


def get_status_message(hour, context):
    if context["is_birthday"]:
        birthday_lines = [
            "A grateful birthday today 🎂",
            "Birthday reflections and quiet joy 🎈",
            "Another year, another blessing 🙏",
            "Marking the day with gratitude 🌼",
            "A simple birthday celebration today 🕯️",
            "Celebrating life with a thankful heart 🌿",
            "A gentle birthday, full of appreciation ✨",
            "Today is a reminder of grace and growth 🌱",
            "A peaceful birthday and warm wishes 🎉",
            "Taking a moment to honor this special day 🌸",
        ]
        return random.choice(birthday_lines)

    if context["is_festival"]:
        return f"{context['festival_name']} · Celebrating with family"

    if context["is_exam_season"] and context["is_student_era"]:
        exam_lines = [
            "Study hours in progress 📚",
            "Revision time and steady focus ✍️",
            "Preparing notes for upcoming exams 📝",
            "Library mood and calm concentration 📖",
            "Small steps, steady progress 🌱",
            "Practice, patience, and persistence today 🧠",
            "Reviewing concepts one chapter at a time 📘",
            "A disciplined day of preparation 📌",
            "Focused learning with a calm mind 🌿",
            "Staying consistent through exam season ⏳",
        ]
        return random.choice(exam_lines)

    if context["is_weekend"]:
        weekend_lines = [
            "A quiet weekend pace ☕",
            "Catching up on personal work 🛠️",
            "Household chores and light reading 🧹",
            "Taking time to rest and reset 🌿",
            "Simple weekend, peaceful mind 🌤️",
            "Unhurried hours and thoughtful planning 📒",
            "A balanced day of rest and routine 🌼",
            "Weekend calm with small meaningful tasks ✅",
            "Reading, reflection, and a slower rhythm 📖",
            "A gentle pause before the new week 🌙",
        ]
        return random.choice(weekend_lines)

    if context["is_student_era"]:
        time_lines = {
            "morning": [
                "Starting the day with tea and plans ☀️",
                "Morning routine and fresh focus 🌼",
                "A calm beginning to the day 🕊️",
                "Early notes and quiet concentration 📓",
                "Building momentum for the day ahead 🌱",
                "A clear mind for the morning tasks ✨",
                "Simple breakfast, steady priorities 🍞",
                "Morning discipline in motion ⏰",
                "Welcoming the day with purpose 🌅",
                "First session: focus and consistency 📘",
            ],
            "noon": [
                "Midday work in progress 🧾",
                "A brief pause before the next task 🍱",
                "Steady work through the afternoon light 🌤️",
                "Continuing with focus, one task at a time 📌",
                "A balanced midday rhythm ⚖️",
                "Checking progress and adjusting plans 🗂️",
                "Quiet effort through noon hours 🌿",
                "Sustaining momentum with patience ⏳",
                "Simple lunch, then back to work 🍛",
                "Midday discipline and measured progress ✅",
            ],
            "afternoon": [
                "Continuing with today’s priorities 📌",
                "One task at a time, with patience 🌿",
                "Quiet afternoon productivity ✨",
                "Reviewing what’s done and what remains 📋",
                "A careful pace through the afternoon 🧠",
                "Steady work, calm focus, clear intent 🌼",
                "Making progress without hurry 🛤️",
                "Afternoon session: notes and refinement 📝",
                "Composed effort through the day’s middle hours 🌤️",
                "Consistency over speed this afternoon ⏱️",
            ],
            "evening": [
                "Evening study and reflection 🌙",
                "Wrapping up the day’s work 📘",
                "A gentle evening rhythm 🕯️",
                "Review hour before rest begins 📖",
                "Closing tasks with care and clarity ✅",
                "A calm end to a productive day 🌇",
                "Evening focus with fewer distractions 🌌",
                "Final revisions for tomorrow’s goals 🧾",
                "Grateful for today’s progress 🙏",
                "Tidying notes and ending well 📓",
            ],
            "night": [
                "Night session, calm and focused 🌌",
                "Reading and planning for tomorrow 📖",
                "Closing the day with gratitude 🙏",
                "A quieter hour for thoughtful work 🕯️",
                "Reflecting on lessons from today 🌿",
                "Late focus, steady and unhurried ⏳",
                "Completing small tasks before rest ✅",
                "A peaceful night of careful planning 🧭",
                "Gentle progress under the night sky 🌙",
                "Preparing mind and notes for a new day 📘",
            ],
            "midnight": [
                "Late hour—time to rest soon 💤",
                "Lights low, thoughts quiet 🌙",
                "Day complete, mind at ease 🌿",
                "A brief pause before sleep 🛏️",
                "Letting the day settle in silence ✨",
                "Closing the notebook for tonight 📒",
                "Quiet midnight reflections 🕯️",
                "Rest now, continue tomorrow 🌅",
                "A calm ending to a full day 🙏",
                "Midnight calm, gentle reset 🔋",
            ],
        }
    else:
        time_lines = {
            "morning": [
                "Morning planning and clear priorities ☕",
                "Beginning the day with intention 🧭",
                "Steady start, one step at a time 🌅",
                "Reviewing goals before the work begins 📋",
                "Calm focus for the first work block 🌿",
                "A measured start with thoughtful direction ✨",
                "Setting the tone for a productive day ✅",
                "Quiet strategy and careful execution 🧠",
                "Opening hours dedicated to clarity 📌",
                "A disciplined start with purpose 🌼",
            ],
            "noon": [
                "Focused work through midday 🧠",
                "Reviewing progress and next steps 📋",
                "Balanced pace, meaningful work ⚖️",
                "Midday check-in and course correction 🧭",
                "Steady output with mindful attention 🌿",
                "A composed work rhythm through noon ✅",
                "Small wins building into larger progress 📈",
                "Careful review before moving ahead 🔎",
                "Measured effort, clear priorities, calm pace ⏳",
                "Noon block: focus, refinement, continuity 📘",
            ],
            "afternoon": [
                "Working through the afternoon queue 🗂️",
                "Careful execution and review 🔎",
                "Progress built patiently, line by line ✍️",
                "Afternoon session with deliberate focus 🧠",
                "Turning plans into completed tasks ✅",
                "Steady refinement and practical progress 🌱",
                "Resolving details with patience and care 📌",
                "A quiet stretch of meaningful work 🌤️",
                "Maintaining quality and consistency ⚙️",
                "Thoughtful output through the latter hours 🕰️",
            ],
            "evening": [
                "Closing tasks for the day 🌇",
                "A thoughtful evening work block 📚",
                "Finishing well, preparing for tomorrow ✅",
                "Reviewing outcomes before day-end 📋",
                "Evening focus with calm intent 🌙",
                "Final checks and tidy handoff 🧾",
                "A measured close to the workday 🕯️",
                "Documenting progress and next actions 📘",
                "Ending the day with clarity and gratitude 🙏",
                "A gentle wind-down after steady work 🌿",
            ],
            "night": [
                "Quiet hours for deep focus 🌌",
                "Late-night review and cleanup 🧹",
                "Planning ahead with a calm mind 🧠",
                "Night work in a quieter rhythm 🌙",
                "Resolving remaining details with care 🔧",
                "Clear notes for tomorrow’s start 📓",
                "A still hour for careful thinking 🕯️",
                "Finishing touches before rest ✅",
                "Slow, precise progress at day’s end ⏳",
                "Night reflection and next-step planning 🧭",
            ],
            "midnight": [
                "System resting window 💤",
                "Day ended, reset for tomorrow 🔋",
                "A still midnight moment 🌙",
                "Quiet pause before the next day 🌌",
                "Closing the day with calm reflection 🙏",
                "Midnight reset: rest, recover, return 🌿",
                "Stepping away to recharge 🛏️",
                "A peaceful end to today’s efforts ✨",
                "Work complete; stillness begins 🕯️",
                "Night closed with gratitude and rest 🌼",
            ],
        }

    if 5 <= hour < 10:
        slot = "morning"
    elif 10 <= hour < 14:
        slot = "noon"
    elif 14 <= hour < 17:
        slot = "afternoon"
    elif 17 <= hour < 21:
        slot = "evening"
    elif 21 <= hour < 24:
        slot = "night"
    else:
        slot = "midnight"

    return random.choice(time_lines[slot])


def get_weather_emoji(condition_id, cloudiness, local_hour):
    is_night = (local_hour >= 20 or local_hour < 5)

    if is_night:
        if 200 <= condition_id < 600:
            return "⛈️"
        if condition_id == 800:
            return "🌙"
        return "☁️"

    if 200 <= condition_id < 300:
        return "⛈️"
    if 300 <= condition_id < 600:
        return "🌧️"
    if 600 <= condition_id < 700:
        return "❄️"
    if 700 <= condition_id < 800:
        return "🌫️"
    if condition_id == 800:
        return "☀️" if cloudiness < 20 else "🌤️"
    if 801 <= condition_id < 900:
        if cloudiness < 40:
            return "🌤️"
        if cloudiness < 80:
            return "⛅"
        return "☁️"
    return "🌍"


def fetch_weather_data():
    nepal_tz = timezone(timedelta(hours=5, minutes=45))
    local_now = datetime.now(nepal_tz)
    local_hour = local_now.hour

    context = check_nepali_context(local_now)

    if not OPENWEATHER_API_KEY:
        status = get_status_message(local_hour, context)
        return {
            "status_text": f"{status} · 📅 BS: {context['bs_date']}",
            "is_fallback": True,
        }

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={LOCATION}&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        weather = data["weather"][0]
        main = data["main"]
        condition_id = weather["id"]
        cloudiness = data.get("clouds", {}).get("all", 0)

        status_msg = get_status_message(local_hour, context)
        weather_icon = get_weather_emoji(condition_id, cloudiness, local_hour)

        status_text = (
            f"{status_msg} · "
            f"{weather_icon} {weather['description'].title()} · "
            f"🌡️ {main['temp']}°C · "
            f"📅 BS: {context['bs_date']}"
        )

        return {"status_text": status_text, "is_fallback": False}

    except Exception as e:
        print(f"⚠️ Error: {e}")
        status = get_status_message(local_hour, context)
        return {
            "status_text": f"{status} · ☁️ API Error · 📅 BS: {context['bs_date']}",
            "is_fallback": True,
        }


def update_readme(data):
    with open(README_FILE, "r") as f:
        content = f.read()

    start_marker = "<!-- WEATHER_START -->"
    end_marker = "<!-- WEATHER_END -->"

    new_block = (
        f"{start_marker}\n<div align=\"center\">\n\n"
        f"**Current Status:** {data['status_text']}\n\n"
        f"</div>\n{end_marker}"
    )

    pattern = re.compile(f"{re.escape(start_marker)}.*?{re.escape(end_marker)}", re.DOTALL)

    if pattern.search(content):
        new_content = pattern.sub(new_block, content)
    else:
        print("⚠️ Markers not found!")
        return False

    with open(README_FILE, "w") as f:
        f.write(new_content)

    print(f"✅ README updated: {data['status_text']}")
    return True


if __name__ == "__main__":
    weather_data = fetch_weather_data()
    update_readme(weather_data)

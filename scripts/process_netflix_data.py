#!/usr/bin/env python3
"""
Netflix Data Processor
Processes raw Netflix data export and generates insights for the Recap report.
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
import re

def parse_duration(duration_str):
    """Convert duration string (HH:MM:SS) to total seconds."""
    if pd.isna(duration_str) or duration_str == "":
        return 0
    try:
        parts = duration_str.split(":")
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return 0
    except:
        return 0

def extract_show_info(title):
    """Extract show name, season, and episode from title."""
    # Pattern: "Show Name: Season X: Episode Title (Episode Y)"
    season_ep_pattern = r'^(.+?):\s*Season\s*(\d+).*?(?:\(Episode\s*(\d+)\))?$'
    # Pattern: "Show Name: Season X_hook" or similar
    hook_pattern = r'^(.+?)(?::\s*Season\s*\d+)?(?:_hook.*|_primary.*)?$'
    
    match = re.match(season_ep_pattern, title)
    if match:
        return {
            'show': match.group(1).strip(),
            'season': int(match.group(2)),
            'episode': int(match.group(3)) if match.group(3) else None,
            'is_episode': True
        }
    
    # Check for movie (no season/episode pattern)
    if ': Season' not in title and ': Episode' not in title:
        # Clean up hook/trailer suffixes
        clean_title = re.sub(r'_hook.*|_primary.*|Clip \d+:|Teaser.*:', '', title)
        return {
            'show': clean_title.strip(),
            'season': None,
            'episode': None,
            'is_episode': False
        }
    
    return {
        'show': title.split(':')[0].strip(),
        'season': None,
        'episode': None,
        'is_episode': False
    }

def get_time_category(hour):
    """Categorize hour into time of day."""
    if 6 <= hour < 12:
        return "Morning (6am-12pm)"
    elif 12 <= hour < 18:
        return "Afternoon (12pm-6pm)"
    elif 18 <= hour < 22:
        return "Evening (6pm-10pm)"
    else:
        return "Night Owl (10pm-6am)"

def determine_personality(stats):
    """Determine viewer personality based on watching patterns."""
    personalities = []
    
    # Calculate key metrics
    night_pct = stats.get('time_categories', {}).get('Night Owl (10pm-6am)', 0)
    total_time = sum(stats.get('time_categories', {}).values()) or 1
    night_ratio = night_pct / total_time
    
    weekend_count = stats.get('day_of_week', {}).get('Saturday', 0) + stats.get('day_of_week', {}).get('Sunday', 0)
    total_dow = sum(stats.get('day_of_week', {}).values()) or 1
    weekend_ratio = weekend_count / total_dow
    
    binge_sessions = stats.get('binge_sessions', 0)
    streak = stats.get('longest_streak', 0)
    unique_shows = stats.get('unique_shows', 0)
    movies = stats.get('movies_watched', 0)
    episodes = stats.get('episodes_watched', 0)
    
    # The Plot Twist Addict - lots of unique shows, doesn't stick to one
    if unique_shows > 100:
        personalities.append(("The Plot Twist Addict", "New show? Sign me up. Your watchlist is basically a buffet."))
    
    # The Marathon Runner - high streak and binge sessions
    if streak > 20 and binge_sessions > 40:
        personalities.append(("The Marathon Runner", "Consistency is your middle name. Rain or shine, you show up for your shows."))
    
    # The After Hours Explorer - late night viewing
    if night_ratio > 0.5:
        personalities.append(("The After Hours Explorer", "The world sleeps, you stream. Some stories just hit different at 2am."))
    
    # The Serial Chiller - high binge count
    if binge_sessions > 50:
        personalities.append(("The Serial Chiller", "One episode is never enough. You don't watch shows, you experience them."))
    
    # The Couch Critic - balanced movies and shows
    if movies > 150 and episodes > 400:
        personalities.append(("The Couch Critic", "Movies, series, documentaries - you appreciate it all. A true connoisseur."))
    
    # The Weekend Wanderer
    if weekend_ratio > 0.4:
        personalities.append(("The Weekend Wanderer", "Saturdays and Sundays are sacred. Your couch knows what's up."))
    
    # The Steady Streamer - consistent active days
    if stats.get('active_days', 0) > 200:
        personalities.append(("The Steady Streamer", "You've made streaming a lifestyle. Netflix is basically a roommate at this point."))
    
    # Default
    if not personalities:
        personalities.append(("The Casual Viewer", "You watch on your own terms. No algorithm can define you."))
    
    # Return the most fitting personality
    return personalities[0]

def generate_fun_facts(stats):
    """Generate fun facts based on viewing statistics."""
    facts = []
    total_hours = stats.get('estimated_hours', 0)
    
    # Hours watched
    if total_hours > 0:
        facts.append({"icon": "clock", "stat": f"{round(total_hours)}", "label": "hours of entertainment"})
    
    # Unique shows explored
    unique = stats.get('unique_shows', 0)
    if unique > 0:
        facts.append({"icon": "grid", "stat": f"{unique}", "label": "different shows explored"})
    
    # Late night viewing
    night_pct = stats.get('time_categories', {}).get('Night Owl (10pm-6am)', 0)
    total = sum(stats.get('time_categories', {}).values()) or 1
    night_pct_val = round((night_pct / total) * 100)
    if night_pct_val > 20:
        facts.append({"icon": "moon", "stat": f"{night_pct_val}%", "label": "late night sessions"})
    
    # Active streaming days
    active = stats.get('active_days', 0)
    if active > 0:
        facts.append({"icon": "calendar", "stat": f"{active}", "label": "days you tuned in"})
    
    return facts[:4]  # Limit to 4 for clean grid

def process_netflix_data(data_dir):
    """Main function to process Netflix data and generate statistics."""
    
    data_path = Path(data_dir)
    
    # Find the data subfolder (Netflix uses account ID as folder name)
    subfolders = [f for f in data_path.iterdir() if f.is_dir() and not f.name.startswith('.')]
    if subfolders:
        data_path = subfolders[0]
    
    viewing_file = data_path / "CONTENT_INTERACTION" / "ViewingActivity.csv"
    ratings_file = data_path / "CONTENT_INTERACTION" / "Ratings.csv"
    
    if not viewing_file.exists():
        print(f"ViewingActivity.csv not found at {viewing_file}")
        return None
    
    # Load viewing data
    df = pd.read_csv(viewing_file)
    
    # Clean column names
    df.columns = df.columns.str.strip()
    
    # Parse dates and durations
    df['Start Time'] = pd.to_datetime(df['Start Time'], errors='coerce')
    df['Duration_Seconds'] = df['Duration'].apply(parse_duration)
    df['Duration_Minutes'] = df['Duration_Seconds'] / 60
    
    # Filter to 2025 only and valid durations
    df = df[df['Start Time'].dt.year == 2025]
    df = df[df['Duration_Seconds'] > 0]
    
    # Filter out very short views (likely previews/hooks) - keep views > 1 minute
    df_meaningful = df[df['Duration_Seconds'] >= 60].copy()
    
    # Filter out supplemental content for main stats
    df_main = df_meaningful[
        (df_meaningful['Supplemental Video Type'].isna()) | 
        (df_meaningful['Supplemental Video Type'] == '')
    ].copy()
    
    # Extract show information
    df_main['show_info'] = df_main['Title'].apply(extract_show_info)
    df_main['Show'] = df_main['show_info'].apply(lambda x: x['show'])
    df_main['Is_Episode'] = df_main['show_info'].apply(lambda x: x['is_episode'])
    
    # Time-based features
    df_main['Hour'] = df_main['Start Time'].dt.hour
    df_main['DayOfWeek'] = df_main['Start Time'].dt.day_name()
    df_main['Month'] = df_main['Start Time'].dt.month_name()
    df_main['Date'] = df_main['Start Time'].dt.date
    df_main['TimeCategory'] = df_main['Hour'].apply(get_time_category)
    
    # Calculate statistics
    total_seconds = df_main['Duration_Seconds'].sum()
    total_hours = total_seconds / 3600
    total_days = total_hours / 24
    
    # Count titles and shows
    total_titles = len(df_main)
    unique_shows = df_main['Show'].nunique()
    
    # Top shows by watch time
    show_time = df_main.groupby('Show')['Duration_Minutes'].sum().sort_values(ascending=False)
    show_count = df_main.groupby('Show').size().sort_values(ascending=False)
    
    top_shows = []
    for show in show_count.head(10).index:
        top_shows.append({
            'title': show,
            'count': int(show_count[show]),
            'minutes': round(show_time.get(show, 0))
        })
    
    # Monthly breakdown
    monthly = df_main.groupby('Month').size()
    month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    monthly_breakdown = {m: int(monthly.get(m, 0)) for m in month_order}
    
    # Day of week breakdown
    dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow = df_main.groupby('DayOfWeek').size()
    day_of_week = {d: int(dow.get(d, 0)) for d in dow_order}
    
    # Time of day breakdown
    time_cats = df_main.groupby('TimeCategory').size()
    time_categories = {
        "Morning (6am-12pm)": int(time_cats.get("Morning (6am-12pm)", 0)),
        "Afternoon (12pm-6pm)": int(time_cats.get("Afternoon (12pm-6pm)", 0)),
        "Evening (6pm-10pm)": int(time_cats.get("Evening (6pm-10pm)", 0)),
        "Night Owl (10pm-6am)": int(time_cats.get("Night Owl (10pm-6am)", 0))
    }
    
    # Active days and streak
    active_dates = sorted(df_main['Date'].unique())
    active_days = len(active_dates)
    
    # Calculate longest streak
    longest_streak = 1
    current_streak = 1
    for i in range(1, len(active_dates)):
        if (active_dates[i] - active_dates[i-1]).days == 1:
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 1
    
    # Binge sessions (4+ episodes of same show in one day)
    daily_show_counts = df_main[df_main['Is_Episode']].groupby(['Date', 'Show']).size()
    binge_sessions = (daily_show_counts >= 4).sum()
    
    # Biggest binge
    if len(daily_show_counts) > 0:
        biggest_binge_idx = daily_show_counts.idxmax()
        biggest_binge = int(daily_show_counts.max())
        biggest_binge_show = biggest_binge_idx[1] if biggest_binge >= 4 else ""
    else:
        biggest_binge = 0
        biggest_binge_show = ""
    
    # Peak month
    peak_month = max(monthly_breakdown, key=monthly_breakdown.get)
    peak_month_count = monthly_breakdown[peak_month]
    
    # Favorite day
    favorite_day = max(day_of_week, key=day_of_week.get)
    favorite_day_count = day_of_week[favorite_day]
    
    # Peak time
    peak_time = max(time_categories, key=time_categories.get)
    
    # Device breakdown
    device_counts = df_main['Device Type'].value_counts()
    top_device = device_counts.index[0] if len(device_counts) > 0 else "Unknown"
    # Simplify device name
    if 'TV' in top_device or 'Smart TV' in top_device:
        top_device = "Smart TV"
    elif 'iPhone' in top_device:
        top_device = "iPhone"
    elif 'Android' in top_device:
        top_device = "Android"
    
    # Movies vs Episodes
    movies_watched = len(df_main[~df_main['Is_Episode']])
    episodes_watched = len(df_main[df_main['Is_Episode']])
    
    # Build stats dictionary
    stats = {
        'year': 2025,
        'total_titles_watched': total_titles,
        'unique_shows': unique_shows,
        'estimated_hours': round(total_hours, 1),
        'estimated_days': round(total_days, 1),
        'number_one_show': top_shows[0]['title'] if top_shows else "Unknown",
        'number_one_count': top_shows[0]['count'] if top_shows else 0,
        'number_one_minutes': top_shows[0]['minutes'] if top_shows else 0,
        'peak_month': peak_month,
        'peak_month_count': peak_month_count,
        'favorite_day': favorite_day,
        'favorite_day_count': favorite_day_count,
        'longest_streak': longest_streak,
        'binge_sessions': int(binge_sessions),
        'biggest_binge': biggest_binge,
        'biggest_binge_show': biggest_binge_show,
        'active_days': active_days,
        'peak_time': peak_time,
        'top_shows': top_shows,
        'monthly_breakdown': monthly_breakdown,
        'day_of_week': day_of_week,
        'time_categories': time_categories,
        'movies_watched': movies_watched,
        'episodes_watched': episodes_watched,
        'top_device': top_device,
        'first_watch_date': str(min(active_dates)),
        'last_watch_date': str(max(active_dates)),
    }
    
    # Determine personality
    personality = determine_personality(stats)
    stats['personality'] = {
        'type': personality[0],
        'description': personality[1]
    }
    
    # Generate fun facts
    stats['fun_facts'] = generate_fun_facts(stats)
    
    return stats

if __name__ == "__main__":
    import sys
    
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    
    print("Processing Netflix data...")
    stats = process_netflix_data(data_dir)
    
    if stats:
        output_file = Path(data_dir) / "recap_stats.json"
        with open(output_file, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"Stats saved to {output_file}")
        print(f"\nQuick Summary:")
        print(f"  Total Watch Time: {stats['estimated_hours']} hours ({stats['estimated_days']} days)")
        print(f"  Titles Watched: {stats['total_titles_watched']}")
        print(f"  Unique Shows: {stats['unique_shows']}")
        print(f"  #1 Show: {stats['number_one_show']} ({stats['number_one_count']} plays)")
        print(f"  Longest Streak: {stats['longest_streak']} days")
        print(f"  Personality: {stats['personality']['type']}")
    else:
        print("Failed to process data")

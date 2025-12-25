"""
Netflix Wrapped - Data Processing Script

This script processes the Netflix viewing history CSV export and generates
statistics for the Wrapped visualization.

To get your Netflix data:
1. Go to Netflix.com > Profile > Account
2. Click "Download your personal information"
3. Wait for the email and download the ZIP
4. Extract ViewingActivity.csv to the data/ folder
"""

import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter
import re


def load_viewing_data(filepath: str) -> pd.DataFrame:
    """Load and clean Netflix viewing history CSV."""
    df = pd.read_csv(filepath)
    
    # Netflix exports typically have these columns
    # Adjust based on actual export format
    expected_cols = ['Title', 'Date']
    
    # Rename columns if needed (Netflix format varies)
    if 'Start Time' in df.columns:
        df = df.rename(columns={'Start Time': 'Date'})
    
    # Parse dates
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # Extract year, month, day of week, hour
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df['MonthName'] = df['Date'].dt.month_name()
    df['DayOfWeek'] = df['Date'].dt.day_name()
    df['Hour'] = df['Date'].dt.hour
    df['WeekOfYear'] = df['Date'].dt.isocalendar().week
    
    # Parse title to extract show name vs episode
    df['ShowName'] = df['Title'].apply(extract_show_name)
    df['IsEpisode'] = df['Title'].str.contains(':', regex=False)
    
    return df


def extract_show_name(title: str) -> str:
    """Extract the main show/movie name from a title."""
    if pd.isna(title):
        return "Unknown"
    
    # Netflix format: "Show Name: Season X: Episode Title"
    # or just "Movie Name"
    parts = str(title).split(':')
    return parts[0].strip()


def calculate_stats(df: pd.DataFrame, year: int = None) -> dict:
    """Calculate all wrapped statistics."""
    
    if year:
        df = df[df['Year'] == year]
    
    if df.empty:
        return {"error": "No data found for the specified year"}
    
    stats = {}
    
    # Basic counts
    stats['total_titles_watched'] = len(df)
    stats['unique_shows'] = df['ShowName'].nunique()
    stats['year'] = year or df['Year'].max()
    
    # Estimate watch time (rough estimate: 45 min per entry)
    stats['estimated_hours'] = round(len(df) * 0.75, 1)
    stats['estimated_days'] = round(stats['estimated_hours'] / 24, 1)
    
    # Top shows
    show_counts = df['ShowName'].value_counts()
    stats['top_shows'] = [
        {'title': show, 'count': int(count)}
        for show, count in show_counts.head(10).items()
    ]
    
    # Number one show
    if len(stats['top_shows']) > 0:
        stats['number_one_show'] = stats['top_shows'][0]['title']
        stats['number_one_count'] = stats['top_shows'][0]['count']
    
    # Monthly breakdown
    monthly = df.groupby('MonthName').size()
    month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    monthly = monthly.reindex(month_order, fill_value=0)
    stats['monthly_breakdown'] = monthly.to_dict()
    
    # Peak month
    if not monthly.empty:
        peak_month = monthly.idxmax()
        stats['peak_month'] = peak_month
        stats['peak_month_count'] = int(monthly[peak_month])
    
    # Day of week breakdown
    dow_counts = df['DayOfWeek'].value_counts()
    dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_counts = dow_counts.reindex(dow_order, fill_value=0)
    stats['day_of_week'] = dow_counts.to_dict()
    
    # Favorite day
    if not dow_counts.empty:
        stats['favorite_day'] = dow_counts.idxmax()
        stats['favorite_day_count'] = int(dow_counts.max())
    
    # Time of day breakdown
    hour_counts = df['Hour'].value_counts().sort_index()
    stats['hourly_breakdown'] = {str(k): int(v) for k, v in hour_counts.items()}
    
    # Categorize viewing times
    morning = df[(df['Hour'] >= 6) & (df['Hour'] < 12)]
    afternoon = df[(df['Hour'] >= 12) & (df['Hour'] < 18)]
    evening = df[(df['Hour'] >= 18) & (df['Hour'] < 22)]
    night = df[(df['Hour'] >= 22) | (df['Hour'] < 6)]
    
    time_cats = {
        'Morning (6am-12pm)': len(morning),
        'Afternoon (12pm-6pm)': len(afternoon),
        'Evening (6pm-10pm)': len(evening),
        'Night Owl (10pm-6am)': len(night)
    }
    stats['time_categories'] = time_cats
    stats['peak_time'] = max(time_cats, key=time_cats.get)
    
    # Binge sessions (3+ episodes of same show in one day)
    daily_shows = df.groupby([df['Date'].dt.date, 'ShowName']).size()
    binges = daily_shows[daily_shows >= 3]
    stats['binge_sessions'] = len(binges)
    stats['biggest_binge'] = int(binges.max()) if len(binges) > 0 else 0
    if len(binges) > 0:
        biggest_binge_idx = binges.idxmax()
        stats['biggest_binge_show'] = biggest_binge_idx[1]
        stats['biggest_binge_date'] = str(biggest_binge_idx[0])
    
    # Streaks - consecutive days of watching
    unique_dates = df['Date'].dt.date.unique()
    unique_dates = sorted(unique_dates)
    
    max_streak = 1
    current_streak = 1
    
    for i in range(1, len(unique_dates)):
        if (unique_dates[i] - unique_dates[i-1]).days == 1:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1
    
    stats['longest_streak'] = max_streak
    stats['active_days'] = len(unique_dates)
    
    # Viewing personality
    stats['personality'] = determine_personality(stats)
    
    # Fun comparisons
    stats['fun_facts'] = generate_fun_facts(stats)
    
    return stats


def determine_personality(stats: dict) -> dict:
    """Determine the viewer's Netflix personality type."""
    
    personality = {
        'type': 'The Casual Viewer',
        'description': 'You enjoy Netflix at a comfortable pace.'
    }
    
    hours = stats.get('estimated_hours', 0)
    binges = stats.get('binge_sessions', 0)
    peak_time = stats.get('peak_time', '')
    streak = stats.get('longest_streak', 0)
    
    if hours > 500:
        personality['type'] = 'The Streaming Champion'
        personality['description'] = 'Netflix might as well be your second home. You have seen it ALL.'
    elif binges > 50:
        personality['type'] = 'The Binge Master'
        personality['description'] = 'One more episode? Make that ten. Sleep is optional when the plot thickens.'
    elif 'Night' in peak_time:
        personality['type'] = 'The Night Owl'
        personality['description'] = 'The best shows come out at night. Or maybe you just lost track of time again.'
    elif streak > 30:
        personality['type'] = 'The Devoted Streamer'
        personality['description'] = 'Rain or shine, you never miss a day. Netflix is part of your daily routine.'
    elif hours > 200:
        personality['type'] = 'The Enthusiast'
        personality['description'] = 'You know what you like and you are not afraid to watch it all.'
    elif 'Morning' in peak_time:
        personality['type'] = 'The Early Bird'
        personality['description'] = 'Coffee and Netflix? You start your days right.'
    
    return personality


def generate_fun_facts(stats: dict) -> list:
    """Generate fun comparison facts."""
    facts = []
    
    hours = stats.get('estimated_hours', 0)
    titles = stats.get('total_titles_watched', 0)
    streak = stats.get('longest_streak', 0)
    binges = stats.get('binge_sessions', 0)
    
    # Time comparisons
    if hours > 0:
        flights_to_tokyo = round(hours / 14, 1)
        facts.append(f"You could have flown to Tokyo {flights_to_tokyo} times with your watch time.")
        
        books = round(hours / 6)
        facts.append(f"In this time, you could have read approximately {books} books. But who is counting?")
        
    if streak > 7:
        facts.append(f"Your {streak}-day streak shows true dedication. Netflix should send you a trophy.")
    
    if binges > 20:
        facts.append(f"With {binges} binge sessions, you have mastered the art of 'just one more episode'.")
    
    if titles > 365:
        facts.append("You watched more titles than there are days in a year. Impressive commitment.")
    
    return facts


def save_stats(stats: dict, output_path: str):
    """Save statistics to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2, default=str)
    print(f"Stats saved to {output_path}")


def main():
    """Main entry point."""
    data_dir = Path(__file__).parent.parent / 'data'
    
    # Look for Netflix viewing history file
    csv_files = list(data_dir.glob('*.csv'))
    
    if not csv_files:
        print("No CSV files found in data/ folder.")
        print("Please download your Netflix viewing history and place it in the data/ folder.")
        print("\nTo get your data:")
        print("1. Go to Netflix.com > Profile > Account")
        print("2. Click 'Download your personal information'")
        print("3. Extract ViewingActivity.csv to the data/ folder")
        return
    
    # Use the first CSV found (or ViewingActivity.csv if it exists)
    viewing_file = data_dir / 'ViewingActivity.csv'
    if not viewing_file.exists():
        viewing_file = csv_files[0]
    
    print(f"Processing: {viewing_file}")
    
    # Load and process data
    df = load_viewing_data(viewing_file)
    print(f"Loaded {len(df)} viewing records")
    
    # Get the most recent full year
    current_year = datetime.now().year
    available_years = df['Year'].unique()
    
    # Calculate stats for most recent year with data
    target_year = 2025 if 2025 in available_years else max([y for y in available_years if y <= current_year])
    
    print(f"Calculating stats for {target_year}...")
    stats = calculate_stats(df, year=target_year)
    
    # Save stats
    output_file = data_dir / 'wrapped_stats.json'
    save_stats(stats, output_file)
    
    print("\nWrapped Stats Summary:")
    print(f"  Year: {stats.get('year')}")
    print(f"  Total watched: {stats.get('total_titles_watched')}")
    print(f"  Estimated hours: {stats.get('estimated_hours')}")
    print(f"  Top show: {stats.get('number_one_show')}")
    print(f"  Personality: {stats.get('personality', {}).get('type')}")


if __name__ == "__main__":
    main()

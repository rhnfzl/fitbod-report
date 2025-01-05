"""Report generation utilities for workout data.

This module provides functionality to generate workout summary reports from processed
workout data. It includes functions to summarize workout data by week and generate
formatted markdown reports.

The module handles both cardio and strength training exercises, calculating various
metrics like total volume, distance, duration, and week-over-week changes.
"""

import pytz
import tzlocal
from datetime import datetime, timedelta
from ..utils.converters import convert_units, seconds_to_time

def get_available_timezones():
    """Get list of common timezones with consolidated regions.
    
    Returns:
        list: List of timezone names organized by region with consolidated similar zones
    """
    
    # Define timezone groups with primary city for each timezone
    timezone_groups = {
        'Europe': {
            # UTC+1 (CET)
            'Europe/Paris': [
        'Europe/Amsterdam',
        'Europe/Berlin',
                'Europe/Brussels',
                'Europe/Copenhagen',
                'Europe/Madrid',
                'Europe/Oslo',
        'Europe/Rome',
                'Europe/Stockholm',
                'Europe/Vienna',
                'Europe/Warsaw',
                'Europe/Zurich'
            ],
            # UTC+0 (GMT/WET)
            'Europe/London': [
                'Europe/Dublin',
                'Europe/Lisbon'
            ],
            # UTC+2 (EET)
            'Europe/Helsinki': [
                'Europe/Athens',
                'Europe/Bucharest',
                'Europe/Sofia'
            ],
            # UTC+3
            'Europe/Moscow': [
                'Europe/Istanbul',
                'Europe/Minsk'
            ]
        },
        'Americas': {
            # UTC-5 (EST)
            'America/New_York': [
                'America/Toronto',
                'America/Detroit',
                'America/Montreal'
            ],
            # UTC-6 (CST)
            'America/Chicago': [
                'America/Mexico_City',
                'America/Winnipeg'
            ],
            # UTC-7 (MST)
            'America/Denver': [
                'America/Phoenix',
                'America/Edmonton'
            ],
            # UTC-8 (PST)
            'America/Los_Angeles': [
                'America/Vancouver',
                'America/Tijuana'
            ],
            'America/Sao_Paulo': [
                'America/Buenos_Aires',
                'America/Santiago'
            ]
        },
        'Asia': {
            'Asia/Dubai': [
                'Asia/Muscat',
                'Asia/Baku'
            ],
            'Asia/Kolkata': [
                'Asia/Colombo'
            ],
            'Asia/Bangkok': [
                'Asia/Jakarta',
                'Asia/Hanoi'
            ],
            'Asia/Shanghai': [
                'Asia/Hong_Kong',
                'Asia/Taipei',
                'Asia/Manila',
                'Asia/Singapore',
                'Asia/Kuala_Lumpur'
            ],
            'Asia/Tokyo': [
                'Asia/Seoul'
            ]
        },
        'Pacific': {
            'Australia/Sydney': [
                'Australia/Melbourne',
                'Australia/Hobart'
            ],
            'Australia/Adelaide': [],
            'Australia/Perth': [],
            'Pacific/Auckland': []
        }
    }
    
    # Build list of primary timezones
    organized_zones = []
    
    # Add timezones by region
    for region, zones in timezone_groups.items():
        # Add primary cities for each region
        for primary_zone in zones.keys():
            organized_zones.append(primary_zone)
    
    # Add UTC at the very end
    organized_zones.append('UTC')
    
    return organized_zones

def detect_timezone(available_timezones):
    """Detect the user's timezone and find the closest match in available timezones.
    
    Args:
        available_timezones (list): List of available timezone names
        
    Returns:
        str: Best matching timezone name from available_timezones
    """
    # System timezone abbreviation to Olson timezone mapping
    system_to_olson = {
        # North America
        'EST': 'America/New_York',
        'EDT': 'America/New_York',
        'CST': 'America/Chicago',
        'CDT': 'America/Chicago',
        'MST': 'America/Denver',
        'MDT': 'America/Denver',
        'PST': 'America/Los_Angeles',
        'PDT': 'America/Los_Angeles',
        'AST': 'America/Halifax',
        'ADT': 'America/Halifax',
        'NST': 'America/St_Johns',
        'NDT': 'America/St_Johns',
        'AKST': 'America/Anchorage',
        'AKDT': 'America/Anchorage',
        'HST': 'Pacific/Honolulu',
        
        # Europe
        'GMT': 'Europe/London',
        'BST': 'Europe/London',
        'WET': 'Europe/London',
        'WEST': 'Europe/Lisbon',
        'CET': 'Europe/Paris',
        'CEST': 'Europe/Paris',
        'EET': 'Europe/Helsinki',
        'EEST': 'Europe/Helsinki',
        'MSK': 'Europe/Moscow',
        'MSD': 'Europe/Moscow',
        
        # Asia
        'IST': 'Asia/Kolkata',
        'PKT': 'Asia/Karachi',
        'BST': 'Asia/Dhaka',
        'SGT': 'Asia/Singapore',
        'CST': 'Asia/Shanghai',
        'JST': 'Asia/Tokyo',
        'KST': 'Asia/Seoul',
        'PHT': 'Asia/Manila',
        'ICT': 'Asia/Bangkok',
        'GST': 'Asia/Dubai',
        
        # Australia & Pacific
        'AEST': 'Australia/Sydney',
        'AEDT': 'Australia/Sydney',
        'ACST': 'Australia/Adelaide',
        'ACDT': 'Australia/Adelaide',
        'AWST': 'Australia/Perth',
        'NZST': 'Pacific/Auckland',
        'NZDT': 'Pacific/Auckland',
        
        # South America
        'ART': 'America/Argentina/Buenos_Aires',
        'BRT': 'America/Sao_Paulo',
        'BRST': 'America/Sao_Paulo',
        'CLT': 'America/Santiago',
        'CLST': 'America/Santiago',
        
        # Africa
        'WAT': 'Africa/Lagos',
        'CAT': 'Africa/Johannesburg',
        'EAT': 'Africa/Nairobi',
        'SAST': 'Africa/Johannesburg'
    }
    
    # Try to get local timezone
    try:
        detected_tz = str(tzlocal.get_localzone())
    except:
        # Fallback to system time if tzlocal fails
        import time
        local_time = time.localtime()
        local_timezone = time.tzname[local_time.tm_isdst]
        detected_tz = system_to_olson.get(local_timezone, available_timezones[0])
    
    # Find best matching timezone
    if detected_tz in available_timezones:
        return detected_tz
    
    # Try to match by region
    detected_region = detected_tz.split('/')[0] if '/' in detected_tz else detected_tz
    for tz in available_timezones:
        if tz.startswith(detected_region + '/'):
            return tz
    
    return available_timezones[0]

def format_timezone_display(tz):
    """Format timezone for display in UI with offset.
    
    Args:
        tz (str): Timezone name
        
    Returns:
        str: Formatted timezone name for display
    """
    try:
        import pytz
        tz_obj = pytz.timezone(tz)
        offset = datetime.now(tz_obj).strftime('%z')
        offset_str = f"{offset[:3]}:{offset[3:]}"
        
        if '/' in tz:
            region, city = tz.split('/', 1)
            return f"{region} - {city.replace('_', ' ')} (UTC{offset_str})"
        return f"{tz} (UTC{offset_str})"
    except:
        # Fallback if timezone operations fail
        if '/' in tz:
            region, city = tz.split('/', 1)
            return f"{region} - {city.replace('_', ' ')}"
        return tz

def summarize_by_week(processed_data, use_metric=True, timezone='UTC'):
    """Generate weekly summaries from processed workout data.
    
    This function processes workout data and generates weekly summaries including:
    - Exercise volumes and distances
    - Total workout durations (cardio and strength)
    - Exercise details and progression
    - Week-over-week changes in key metrics
    
    Args:
        processed_data (list): List of workout entries with exercise details
        use_metric (bool): Whether to use metric units (True) or imperial units (False)
        timezone (str): Timezone to use for date calculations
    
    Returns:
        dict: Weekly summaries containing workout statistics and exercise details
    """
    summaries = {}
    tz = pytz.timezone(timezone)
    
    # First, organize and clean data by date
    workouts_by_date = {}
    for entry in processed_data:
        # Clean up date string and parse it - handle various date formats
        date_str = entry['Date']
        if '+' in date_str:
            # Remove timezone if present to standardize format
            date_str = date_str.split('+')[0].strip()
        
        try:
            # Try parsing with timezone first
            date_utc = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                # Try parsing without seconds
                date_utc = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
            except ValueError:
                # Fall back to just date
                date_utc = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Convert to local timezone for consistent date handling
        local_date = date_utc.replace(tzinfo=pytz.UTC).astimezone(tz)
        workout_date = local_date.strftime('%Y-%m-%d')
        week_start = local_date - timedelta(days=local_date.weekday())
        week_key = week_start.strftime('%Y-%m-%d') + ' to ' + (week_start + timedelta(days=6)).strftime('%Y-%m-%d')
        
        # Extract exercise metrics - store original weight
        weight = float(entry['Weight(kg)'])  # Keep original weight
        reps = int(float(entry['Reps']))
        distance_m = float(entry['Distance(m)'])
        try:
            duration = float(entry['Duration(s)']) if entry['Duration(s)'] else 0.0
        except (ValueError, TypeError):
            duration = 0.0
        
        # Convert weight if using imperial
        if not use_metric:
            weight, _ = convert_units(weight, 'weight', to_metric=False)
            # Store the rounded weight for volume calculations
            rounded_weight = weight
        else:
            rounded_weight = weight
        
        # Classify exercise type based on metrics
        is_cardio = (
            (duration > 0 and distance_m > 0) or  # Running, Walking etc
            (reps == 0 and distance_m == 0 and duration > 300)  # Elliptical, Rowing etc
        )
        
        # Strength exercises are anything not cardio meeting specific criteria
        is_strength = not is_cardio and (
            (reps == 0 and weight > 0) or  # Kettlebell Single Arm Farmer Walk, Sled Push etc
            (reps > 0 and weight == 0 and duration == 0) or  # Air Squats, Bench Dip etc
            (reps > 0 and weight > 0) or  # Deadlift, Cable Face Pull etc
            (reps > 0 and distance_m == 0) or  # Bent Over Barbell Row etc
            (reps == 0 and distance_m == 0)  # Dead Hang, Plank etc
        )
        
        # Create cleaned entry with additional metadata
        cleaned_entry = {
            **entry,
            'local_datetime': local_date,
            'is_cardio': is_cardio,
            'is_strength': is_strength,
            'duration': duration,
            'weight': rounded_weight,  # Use rounded weight
            'weight_unit': 'lbs' if not use_metric else 'kg',
            'reps': reps,
            'distance_m': distance_m
        }
        
        # Initialize workout data structure if needed
        if workout_date not in workouts_by_date:
            workouts_by_date[workout_date] = {
                'exercises': [],
                'week_key': week_key,
                'strength_sessions': []  # List to track strength training sessions
            }
        
        workout_data = workouts_by_date[workout_date]
        workout_data['exercises'].append(cleaned_entry)
        
        # Track strength training sessions
        if is_strength:
            # Check if this exercise belongs to an existing session
            session_found = False
            for session in workout_data['strength_sessions']:
                last_exercise = session[-1]
                time_gap = (local_date - last_exercise['local_datetime']).total_seconds()
                
                # If exercise is within 30 minutes of last exercise, add to session
                if time_gap <= 1800:  # 30 minutes in seconds
                    session.append(cleaned_entry)
                    session_found = True
                    break
            
            # If no suitable session found, start a new one
            if not session_found:
                workout_data['strength_sessions'].append([cleaned_entry])
    
    # Initialize summaries for each week
    for workout_date, workout_data in workouts_by_date.items():
        week_key = workout_data['week_key']
        if week_key not in summaries:
            summaries[week_key] = {
                'cardio_duration': 0,
                'strength_duration': 0,  # Will be calculated from sessions
                'Distance': 0,
                'Reps': 0,
                'Volume': 0,
                'Distance_by_exercise': {},
                'Volume_by_exercise': {},
                'Exercise_details': {},
                'Workouts': {}
            }
        
        # Calculate strength duration from sessions
        for session in workout_data['strength_sessions']:
            if len(session) > 0:
                # Get unique timestamps to check if we need to estimate duration
                unique_timestamps = len(set(ex['local_datetime'] for ex in session))
                
                if unique_timestamps > 1:
                    # If we have different timestamps, use them
                    session_start = session[0]['local_datetime']
                    session_end = session[-1]['local_datetime']
                    session_duration = (session_end - session_start).total_seconds()
                else:
                    # If all timestamps are identical, estimate duration
                    # Assume average of 2 minutes per exercise for working sets
                    # And 1 minute per exercise for warmup sets
                    session_duration = sum(
                        120 if ex['isWarmup'].lower() != 'true' else 60 
                        for ex in session
                    )
                
                summaries[week_key]['strength_duration'] += session_duration
    
    # Process each day's exercises for other statistics
    for workout_date, workout_data in workouts_by_date.items():
        week_key = workout_data['week_key']
        
        # Process exercises for other statistics
        for exercise in workout_data['exercises']:
            # Add to workouts timeline
            workout_time = exercise['local_datetime'].strftime('%Y-%m-%d %H:%M')
            if workout_time not in summaries[week_key]['Workouts']:
                summaries[week_key]['Workouts'][workout_time] = []
            
            # Convert units for display
            weight, weight_unit = convert_units(exercise['weight'], 'weight', use_metric)
            
            # Create exercise detail
            exercise_detail = {
                'exercise': exercise['Exercise'],
                'weight': weight,
                'weight_unit': weight_unit,
                'reps': exercise['reps'],
                'is_warmup': exercise['isWarmup'].lower() == 'true',
                'time': exercise['local_datetime'].strftime('%H:%M'),
                'duration': exercise['duration'],
                'is_cardio': exercise['is_cardio']
            }
            
            summaries[week_key]['Workouts'][workout_time].append(exercise_detail)
            
            # Update summary statistics
            summaries[week_key]['Reps'] += exercise['reps']
            
            if exercise['is_cardio']:
                summaries[week_key]['cardio_duration'] += exercise['duration']
            
            # Update exercise details
            if exercise['Exercise'] not in summaries[week_key]['Exercise_details']:
                summaries[week_key]['Exercise_details'][exercise['Exercise']] = {
                    'sets': [],
                    'total_volume': 0,
                    'max_weight': 0,
                    'total_reps': 0,
                    'total_duration': 0,
                    'working_sets': 0,
                    'warmup_sets': 0,
                    'is_cardio': exercise['is_cardio']
                }
            
            details = summaries[week_key]['Exercise_details'][exercise['Exercise']]
            details['sets'].append({
                'weight': exercise['weight'],  # Already rounded
                'reps': exercise['reps'],
                'is_warmup': exercise['isWarmup'].lower() == 'true',
                'duration': exercise['duration'],
                'is_cardio': exercise['is_cardio']
            })
            # Calculate volume using rounded weight
            volume = exercise['weight'] * exercise['reps']
            details['total_volume'] += volume
            details['max_weight'] = max(details['max_weight'], exercise['weight'])
            details['total_reps'] += exercise['reps']
            details['total_duration'] += exercise['duration']
            
            if exercise['isWarmup'].lower() == 'true':
                details['warmup_sets'] += 1
            else:
                details['working_sets'] += 1
            
            # Convert and accumulate distance
            distance_km = exercise['distance_m'] / 1000
            distance, _ = convert_units(distance_km, 'distance', use_metric)
            summaries[week_key]['Distance'] += distance
            
            # Add to distance by exercise if applicable
            if distance > 0:
                if exercise['Exercise'] not in summaries[week_key]['Distance_by_exercise']:
                    summaries[week_key]['Distance_by_exercise'][exercise['Exercise']] = 0
                summaries[week_key]['Distance_by_exercise'][exercise['Exercise']] += distance
            
            # Add to volume by exercise if applicable
            volume = exercise['weight'] * exercise['reps']  # Use rounded weight consistently
            summaries[week_key]['Volume'] += volume
            if volume > 0:
                if exercise['Exercise'] not in summaries[week_key]['Volume_by_exercise']:
                    summaries[week_key]['Volume_by_exercise'][exercise['Exercise']] = 0
                summaries[week_key]['Volume_by_exercise'][exercise['Exercise']] += volume
    
    return summaries

def aggregate_summaries(summaries, period_type):
    """Aggregate weekly summaries into larger periods.
    
    Args:
        summaries (dict): Weekly summaries from summarize_by_week()
        period_type (str): Type of period to aggregate into ('monthly', '4-weeks', '8-weeks', '12-weeks', '24-weeks')
        
    Returns:
        dict: Aggregated summaries by period
    """
    sorted_weeks = sorted(summaries.keys(), 
                         key=lambda x: datetime.strptime(x.split(' to ')[0], '%Y-%m-%d'))
    
    if not sorted_weeks:
        return {}
        
    aggregated = {}
    
    # Get the first week's start date
    first_week_start = datetime.strptime(sorted_weeks[0].split(' to ')[0], '%Y-%m-%d')
    
    for week in sorted_weeks:
        week_start = datetime.strptime(week.split(' to ')[0], '%Y-%m-%d')
        week_summary = summaries[week]
        
        if period_type == 'monthly':
            # Group by calendar month
            period_key = week_start.strftime('%Y-%m')
            period_name = f"{week_start.strftime('%B %Y')}"
        else:
            # For n-week periods, calculate based on weeks from start
            weeks_number = int(period_type.split('-')[0])
            period_number = (week_start - first_week_start).days // (7 * weeks_number)
            period_start = first_week_start + timedelta(days=period_number * 7 * weeks_number)
            period_end = period_start + timedelta(days=7 * weeks_number - 1)
            period_key = period_start.strftime('%Y-%m-%d')
            period_name = f"{period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"
        
        if period_key not in aggregated:
            aggregated[period_key] = {
                'period_name': period_name,
                'cardio_duration': 0,
                'strength_duration': 0,
                'Distance': 0,
                'Reps': 0,
                'Volume': 0,
                'Distance_by_exercise': {},
                'Volume_by_exercise': {},
                'Exercise_details': {},
                'Workouts': {},
                'weeks': []
            }
        
        period_summary = aggregated[period_key]
        period_summary['weeks'].append(week)
        
        # Aggregate numeric metrics
        period_summary['cardio_duration'] += week_summary.get('cardio_duration', 0)
        period_summary['strength_duration'] += week_summary.get('strength_duration', 0)
        period_summary['Distance'] += week_summary.get('Distance', 0)
        period_summary['Reps'] += week_summary.get('Reps', 0)
        period_summary['Volume'] += week_summary.get('Volume', 0)
        
        # Aggregate exercise-specific metrics
        for exercise, distance in week_summary.get('Distance_by_exercise', {}).items():
            if exercise not in period_summary['Distance_by_exercise']:
                period_summary['Distance_by_exercise'][exercise] = 0
            period_summary['Distance_by_exercise'][exercise] += distance
            
        for exercise, volume in week_summary.get('Volume_by_exercise', {}).items():
            if exercise not in period_summary['Volume_by_exercise']:
                period_summary['Volume_by_exercise'][exercise] = 0
            period_summary['Volume_by_exercise'][exercise] += volume
        
        # Aggregate detailed workout information
        for workout_time, exercises in week_summary.get('Workouts', {}).items():
            period_summary['Workouts'][workout_time] = exercises
        
        # Aggregate exercise details
        for exercise, details in week_summary.get('Exercise_details', {}).items():
            if exercise not in period_summary['Exercise_details']:
                period_summary['Exercise_details'][exercise] = {
                    'sets': [],
                    'total_volume': 0,
                    'max_weight': 0,
                    'total_reps': 0,
                    'total_duration': 0,
                    'working_sets': 0,
                    'warmup_sets': 0,
                    'is_cardio': details['is_cardio']
                }
            
            ex_details = period_summary['Exercise_details'][exercise]
            ex_details['sets'].extend(details['sets'])
            ex_details['total_volume'] += details['total_volume']
            ex_details['max_weight'] = max(ex_details['max_weight'], details['max_weight'])
            ex_details['total_reps'] += details['total_reps']
            ex_details['total_duration'] += details.get('total_duration', 0)
            ex_details['working_sets'] += details['working_sets']
            ex_details['warmup_sets'] += details['warmup_sets']
    
    return aggregated

def generate_period_summary(period_name, period_summary, use_metric, previous_period_summary=None, report_format='summary'):
    """Generate markdown summary for a specific period.
    
    Args:
        period_name (str): Name of the period
        period_summary (dict): Summary data for the period
        use_metric (bool): Whether to use metric units
        previous_period_summary (dict): Previous period's summary for comparison
        report_format (str): Type of report to generate ('summary' or 'detailed')
        
    Returns:
        list: Lines of markdown text for the period summary
    """
    _, distance_unit = convert_units(1, 'distance', use_metric)
    weight_unit = 'kg' if use_metric else 'lbs'
    
    lines = []
    lines.append(f"## {period_name}\n")
    
    if report_format == 'detailed':
        # Daily Workouts
        lines.append("### Daily Workouts\n")
        for workout_time in sorted(period_summary['Workouts'].keys()):
            date = workout_time.split()[0]
            lines.append(f"#### {date}\n")
            
            # Group exercises by name
            exercises_by_name = {}
            for exercise in period_summary['Workouts'][workout_time]:
                if exercise['exercise'] not in exercises_by_name:
                    exercises_by_name[exercise['exercise']] = []
                exercises_by_name[exercise['exercise']].append(exercise)
            
            # Show exercises grouped
            for exercise_name in sorted(exercises_by_name.keys()):
                exercise_sets = exercises_by_name[exercise_name]
                lines.append(f"**{exercise_name}** ({len(exercise_sets)} sets)")
                lines.append("| Set | Reps | Weight | Type |")
                lines.append("|-----|------|---------|------|")
                
                for i, set_info in enumerate(exercise_sets, 1):
                    lines.append(f"| {i} | {set_info['reps']} | "
                               f"{set_info['weight']:.1f} {set_info['weight_unit']} | "
                               f"{'Warmup' if set_info['is_warmup'] else 'Working'} |")
                lines.append("")
        
        # Exercise Details
        lines.append("### Exercise Details\n")
        for exercise_name in sorted(period_summary['Exercise_details'].keys()):
            details = period_summary['Exercise_details'][exercise_name]
            lines.append(f"#### {exercise_name}")
            lines.append(f"- Working Sets: {details['working_sets']}")
            lines.append(f"- Warmup Sets: {details['warmup_sets']}")
            lines.append(f"- Total Reps: {details['total_reps']}")
            if details['is_cardio']:
                lines.append(f"- Total Duration: {seconds_to_time(details['total_duration'])}")
            lines.append(f"- Max Weight: {details['max_weight']:.1f} {weight_unit}")
            lines.append(f"- Total Volume: {details['total_volume']:.1f} {weight_unit}*reps")
            
            # Show set progression
            lines.append("\nSet Progression:")
            lines.append("| Set | Weight | Reps | Type |")
            lines.append("|-----|---------|------|------|")
            
            # Sort sets by date and time
            sorted_sets = sorted(details['sets'], key=lambda x: (x['is_warmup'], -x['weight']))
            for i, set_info in enumerate(sorted_sets, 1):
                lines.append(f"| {i} | {set_info['weight']:.1f} {weight_unit} | "
                           f"{set_info['reps']} | "
                           f"{'Warmup' if set_info['is_warmup'] else 'Working'} |")
            lines.append("")
    else:
        # Summary report with just the key metrics
        if period_summary['Distance_by_exercise']:
            lines.append("### Distance by Exercise")
            for exercise, distance in sorted(period_summary['Distance_by_exercise'].items()):
                lines.append(f"- {exercise}: {distance:.2f} {distance_unit}")
            lines.append("")
        
        if period_summary['Volume_by_exercise']:
            lines.append("### Volume by Exercise")
            for exercise, volume in sorted(period_summary['Volume_by_exercise'].items()):
                lines.append(f"- {exercise}: {volume:.2f} {weight_unit}*reps")
            lines.append("")
    
    # Summary Statistics (included in both formats)
    lines.append("### Summary Statistics")
    
    # Get durations
    cardio_duration = period_summary.get('cardio_duration', 0)
    strength_duration = period_summary.get('strength_duration', 0)
    total_duration = cardio_duration + strength_duration
    
    lines.append(f"- Total Workout Time: {seconds_to_time(total_duration)}")
    lines.append(f"- Strength Training Time: {seconds_to_time(strength_duration)}")
    lines.append(f"- Cardio Time: {seconds_to_time(cardio_duration)}")
    lines.append(f"- Total Distance: {period_summary.get('Distance', 0):.2f} {distance_unit}")
    lines.append(f"- Total Reps: {period_summary.get('Reps', 0)}")
    lines.append(f"- Total Volume: {period_summary.get('Volume', 0):.2f} {weight_unit}*reps")
    
    # Period-over-period changes
    if previous_period_summary:
        prev_distance = previous_period_summary.get('Distance', 0)
        prev_volume = previous_period_summary.get('Volume', 0)
        
        if prev_distance != 0:
            distance_change = ((period_summary.get('Distance', 0) - prev_distance) / prev_distance * 100)
            lines.append(f"- Distance Change: {distance_change:.2f}%")
            
        if prev_volume != 0:
            volume_change = ((period_summary.get('Volume', 0) - prev_volume) / prev_volume * 100)
            lines.append(f"- Volume Change: {volume_change:.2f}%")
    
    lines.append("\n---\n")
    return lines

def generate_markdown_report(summaries, use_metric=True, report_format='summary', period_type=None):
    """Generate markdown report from workout summaries.
    
    Args:
        summaries (dict): Weekly workout summaries from summarize_by_week()
        use_metric (bool): Whether to use metric units (True) or imperial units (False)
        report_format (str): Type of report to generate ('summary' or 'detailed')
        period_type (str): Type of period to aggregate into (None, 'monthly', '4-weeks', etc.)
        
    Returns:
        str: Markdown formatted report containing workout statistics and analysis
    """
    report = ["# Workout Summary Report\n"]
    
    # Define units once for use throughout the report
    _, distance_unit = convert_units(1, 'distance', use_metric)
    weight_unit = 'kg' if use_metric else 'lbs'
    
    # Pre-process exercise data for detailed reports to avoid repeated operations
    exercise_data = {}
    if report_format == 'detailed':
        for week, summary in summaries.items():
            exercise_data[week] = {
                'by_date': {},
                'details': {}
            }
            # Group exercises by date
            for workout_time, exercises in summary.get('Workouts', {}).items():
                date = workout_time.split()[0]
                if date not in exercise_data[week]['by_date']:
                    exercise_data[week]['by_date'][date] = {}
                
                for exercise in exercises:
                    exercise_name = exercise['exercise']
                    if exercise_name not in exercise_data[week]['by_date'][date]:
                        exercise_data[week]['by_date'][date][exercise_name] = []
                    exercise_data[week]['by_date'][date][exercise_name].append(exercise)
            
            # Pre-process exercise details
            for exercise, details in summary.get('Exercise_details', {}).items():
                exercise_data[week]['details'][exercise] = {
                    'working_sets': details['working_sets'],
                    'warmup_sets': details['warmup_sets'],
                    'total_reps': details['total_reps'],
                    'is_cardio': details['is_cardio'],
                    'total_duration': details.get('total_duration', 0),
                    'max_weight': details['max_weight'],
                    'total_volume': details['total_volume'],
                    'sets': sorted(details['sets'], key=lambda x: (x['is_warmup'], -x['weight']))
                }
    
    # Calculate overall totals
    overall_summary = {
        'cardio_duration': 0,
        'strength_duration': 0,
        'Distance': 0,
        'Reps': 0,
        'Volume': 0,
        'Distance_by_exercise': {},
        'Volume_by_exercise': {},
        'start_date': None,
        'end_date': None
    }
    
    # Get all weeks sorted by date
    sorted_weeks = sorted(summaries.keys(), 
                         key=lambda x: datetime.strptime(x.split(' to ')[0], '%Y-%m-%d'))
    
    if sorted_weeks:
        # Set date range
        overall_summary['start_date'] = sorted_weeks[0].split(' to ')[0]
        overall_summary['end_date'] = sorted_weeks[-1].split(' to ')[1]
        
        # Aggregate all metrics
        for week in sorted_weeks:
            summary = summaries[week]
            overall_summary['cardio_duration'] += summary.get('cardio_duration', 0)
            overall_summary['strength_duration'] += summary.get('strength_duration', 0)
            overall_summary['Distance'] += summary.get('Distance', 0)
            overall_summary['Reps'] += summary.get('Reps', 0)
            overall_summary['Volume'] += summary.get('Volume', 0)
            
            # Aggregate exercise-specific metrics
            for exercise, distance in summary.get('Distance_by_exercise', {}).items():
                if exercise not in overall_summary['Distance_by_exercise']:
                    overall_summary['Distance_by_exercise'][exercise] = 0
                overall_summary['Distance_by_exercise'][exercise] += distance
                
            for exercise, volume in summary.get('Volume_by_exercise', {}).items():
                if exercise not in overall_summary['Volume_by_exercise']:
                    overall_summary['Volume_by_exercise'][exercise] = 0
                overall_summary['Volume_by_exercise'][exercise] += volume
    
    # Generate period summaries if requested and not weekly
    if period_type and period_type != "weekly":
        period_summaries = aggregate_summaries(summaries, period_type)
        sorted_periods = sorted(period_summaries.keys())
        
        report.append(f"# {period_type.title()} Summary\n")
        previous_period_summary = None
        for period_key in sorted_periods:
            period_summary = period_summaries[period_key]
            period_lines = generate_period_summary(
                period_summary['period_name'],
                period_summary,
                use_metric,
                previous_period_summary,
                report_format
            )
            report.extend(period_lines)
            previous_period_summary = period_summary
    
    # Generate weekly summaries if period_type is weekly
    if period_type == "weekly":
        previous_week_summary = None
        for week in sorted_weeks:
            summary = summaries[week]
            report.append(f"## Week: {week}\n")
            
            if report_format == 'detailed':
                # Use pre-processed exercise data for detailed report
                report.append("### Daily Workouts\n")
                for workout_date in sorted(exercise_data[week]['by_date'].keys()):
                    report.append(f"#### {workout_date}\n")
                    
                    # Show exercises grouped (already pre-processed)
                    for exercise_name in sorted(exercise_data[week]['by_date'][workout_date].keys()):
                        exercise_sets = exercise_data[week]['by_date'][workout_date][exercise_name]
                    report.append(f"**{exercise_name}** ({len(exercise_sets)} sets)")
                    report.append("| Set | Reps | Weight | Type |")
                    report.append("|-----|------|---------|------|")
                    
                    for i, set_info in enumerate(exercise_sets, 1):
                        report.append(f"| {i} | {set_info['reps']} | "
                                    f"{set_info['weight']:.1f} {set_info['weight_unit']} | "
                                    f"{'Warmup' if set_info['is_warmup'] else 'Working'} |")
                    report.append("")
                
                # Exercise Details (using pre-processed data)
                report.append("### Exercise Details\n")
                for exercise_name in sorted(exercise_data[week]['details'].keys()):
                    details = exercise_data[week]['details'][exercise_name]
                    report.append(f"#### {exercise_name}")
                    report.append(f"- Working Sets: {details['working_sets']}")
                    report.append(f"- Warmup Sets: {details['warmup_sets']}")
                    report.append(f"- Total Reps: {details['total_reps']}")
                    if details['is_cardio']:
                        report.append(f"- Total Duration: {seconds_to_time(details['total_duration'])}")
                    report.append(f"- Max Weight: {details['max_weight']:.1f} {weight_unit}")
                    report.append(f"- Total Volume: {details['total_volume']:.1f} {weight_unit}*reps")
                    
                    # Show set progression
                    report.append("\nSet Progression:")
                    report.append("| Set | Weight | Reps | Type |")
                    report.append("|-----|---------|------|------|")
                    
                    for i, set_info in enumerate(details['sets'], 1):
                        report.append(f"| {i} | {set_info['weight']:.1f} {weight_unit} | "
                                    f"{set_info['reps']} | "
                                    f"{'Warmup' if set_info['is_warmup'] else 'Working'} |")
                    report.append("")
            else:
                # Summary report with just the key metrics
                if summary['Distance_by_exercise']:
                    report.append("### Distance by Exercise")
                    for exercise, distance in sorted(summary['Distance_by_exercise'].items()):
                        report.append(f"- {exercise}: {distance:.2f} {distance_unit}")
                    report.append("")
                
                if summary['Volume_by_exercise']:
                    report.append("### Volume by Exercise")
                    for exercise, volume in sorted(summary['Volume_by_exercise'].items()):
                        report.append(f"- {exercise}: {volume:.2f} {weight_unit}*reps")
                    report.append("")
            
            # Summary statistics (included in both formats)
            report.append("### Summary Statistics")
            
            # Get durations
            cardio_duration = summary.get('cardio_duration', 0)
            strength_duration = summary.get('strength_duration', 0)
            total_duration = cardio_duration + strength_duration
            
            # Always show all durations
            report.append(f"- Total Workout Time: {seconds_to_time(total_duration)}")
            report.append(f"- Strength Training Time: {seconds_to_time(strength_duration)}")
            report.append(f"- Cardio Time: {seconds_to_time(cardio_duration)}")
            
            # Always show these statistics
            report.append(f"- Total Distance: {summary.get('Distance', 0):.2f} {distance_unit}")
            report.append(f"- Total Reps: {summary.get('Reps', 0)}")
            report.append(f"- Total Volume: {summary.get('Volume', 0):.2f} {weight_unit}*reps")
            
            # Week-over-week changes
            if previous_week_summary:
                prev_distance = previous_week_summary.get('Distance', 0)
                prev_volume = previous_week_summary.get('Volume', 0)
                
                distance_change = ((summary.get('Distance', 0) - prev_distance) / prev_distance * 100) if prev_distance != 0 else 0
                volume_change = ((summary.get('Volume', 0) - prev_volume) / prev_volume * 100) if prev_volume != 0 else 0
                
                report.append(f"- Distance Change: {distance_change:.2f}%")
                report.append(f"- Volume Change: {volume_change:.2f}%")
            
            report.append("\n---\n")
            previous_week_summary = summary
    
    # Add overall summary at the end with clear separation
    report.append(f"\n# Overall Summary for {overall_summary['start_date']} to {overall_summary['end_date']}\n")
    
    # Distance by Exercise
    if overall_summary['Distance_by_exercise']:
        report.append("### Total Distance by Exercise")
        for exercise, distance in sorted(overall_summary['Distance_by_exercise'].items()):
            report.append(f"- {exercise}: {distance:.2f} {distance_unit}")
        report.append("")
    
    # Volume by Exercise
    if overall_summary['Volume_by_exercise']:
        report.append("### Total Volume by Exercise")
        for exercise, volume in sorted(overall_summary['Volume_by_exercise'].items()):
            report.append(f"- {exercise}: {volume:.2f} {weight_unit}*reps")
        report.append("")
    
    # Overall Summary Statistics
    report.append("### Overall Summary Statistics")
    
    # Get durations
    total_cardio_duration = overall_summary['cardio_duration']
    total_strength_duration = overall_summary['strength_duration']
    total_duration = total_cardio_duration + total_strength_duration
    
    report.append(f"- Total Workout Time: {seconds_to_time(total_duration)}")
    report.append(f"- Total Strength Training Time: {seconds_to_time(total_strength_duration)}")
    report.append(f"- Total Cardio Time: {seconds_to_time(total_cardio_duration)}")
    report.append(f"- Total Distance: {overall_summary['Distance']:.2f} {distance_unit}")
    report.append(f"- Total Reps: {overall_summary['Reps']}")
    report.append(f"- Total Volume: {overall_summary['Volume']:.2f} {weight_unit}*reps")
    
    # Calculate averages per week
    num_weeks = len(sorted_weeks)
    if num_weeks > 0:
        report.append("\n### Weekly Averages")
        report.append(f"- Average Workout Time: {seconds_to_time(total_duration / num_weeks)}")
        report.append(f"- Average Strength Training Time: {seconds_to_time(total_strength_duration / num_weeks)}")
        report.append(f"- Average Cardio Time: {seconds_to_time(total_cardio_duration / num_weeks)}")
        report.append(f"- Average Distance: {(overall_summary['Distance'] / num_weeks):.2f} {distance_unit}")
        report.append(f"- Average Reps: {int(overall_summary['Reps'] / num_weeks)}")
        report.append(f"- Average Volume: {(overall_summary['Volume'] / num_weeks):.2f} {weight_unit}*reps")
    
    return "\n".join(report) 
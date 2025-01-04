"""Report generation utilities for workout data.

This module provides functionality to generate workout summary reports from processed
workout data. It includes functions to summarize workout data by week and generate
formatted markdown reports.

The module handles both cardio and strength training exercises, calculating various
metrics like total volume, distance, duration, and week-over-week changes.
"""

import pytz
from datetime import datetime, timedelta
from ..utils.converters import convert_units, seconds_to_time

def get_available_timezones():
    """Get list of common timezones with European defaults first.
    
    Returns:
        list: List of timezone names organized by region
    """
    import pytz
    
    # Define preferred European timezones to show first
    preferred_eu_zones = [
        'Europe/Amsterdam',
        'Europe/Berlin',
        'Europe/Paris',
        'Europe/London',
        'Europe/Rome',
        'Europe/Madrid'
    ]
    
    # Common timezone regions we want to include
    common_regions = {
        'Europe': [],
        'US': [],
        'Asia': [],
        'Australia': [],
        'Pacific': []
    }
    
    # Get all timezones and organize them
    for tz in pytz.all_timezones:
        region = tz.split('/', 1)[0]
        if region in common_regions:
            common_regions[region].append(tz)
    
    # Start with preferred European zones
    organized_zones = preferred_eu_zones.copy()
    
    # Add remaining timezones by region
    for region, zones in common_regions.items():
        # Sort zones within each region
        zones.sort()
        # For Europe, exclude zones already in preferred list
        if region == 'Europe':
            zones = [tz for tz in zones if tz not in preferred_eu_zones]
        organized_zones.extend(zones)
    
    # Add UTC at the very end
    organized_zones.append('UTC')
    
    return organized_zones

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
            'weight': weight,  # Store converted weight if imperial
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
                'weight': weight,
                'reps': exercise['reps'],
                'is_warmup': exercise['isWarmup'].lower() == 'true',
                'duration': exercise['duration'],
                'is_cardio': exercise['is_cardio']
            })
            details['total_volume'] += weight * exercise['reps']
            details['max_weight'] = max(details['max_weight'], weight)
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
            volume = weight * exercise['reps']
            summaries[week_key]['Volume'] += volume
            if volume > 0:
                if exercise['Exercise'] not in summaries[week_key]['Volume_by_exercise']:
                    summaries[week_key]['Volume_by_exercise'][exercise['Exercise']] = 0
                summaries[week_key]['Volume_by_exercise'][exercise['Exercise']] += volume
    
    return summaries

def generate_markdown_report(summaries, use_metric=True, report_format='summary'):
    """Generate markdown report from workout summaries.
    
    This function takes the workout summaries and generates a formatted markdown report
    that includes weekly statistics, exercise details, and progress tracking.
    
    Args:
        summaries (dict): Weekly workout summaries from summarize_by_week()
        use_metric (bool): Whether to use metric units (True) or imperial units (False)
        report_format (str): Type of report to generate ('summary' or 'detailed')
        
    Returns:
        str: Markdown formatted report containing workout statistics and analysis
    """
    _, distance_unit = convert_units(1, 'distance', use_metric)
    weight_unit = 'kg' if use_metric else 'lbs'
    
    report = ["# Workout Summary Report\n"]
    
    sorted_weeks = sorted(summaries.keys(), 
                         key=lambda x: datetime.strptime(x.split(' to ')[0], '%Y-%m-%d'))
    
    previous_week_summary = None
    for week in sorted_weeks:
        summary = summaries[week]
        report.append(f"## Week: {week}\n")
        
        if report_format == 'detailed':
            # Detailed report with daily workouts and exercise details
            report.append("### Daily Workouts\n")
            for workout_date, exercises in sorted(summary['Workouts'].items()):
                report.append(f"#### {workout_date}\n")
                
                # Group exercises by name
                exercises_by_name = {}
                for exercise in exercises:
                    if exercise['exercise'] not in exercises_by_name:
                        exercises_by_name[exercise['exercise']] = []
                    exercises_by_name[exercise['exercise']].append(exercise)
                
                # Show exercises grouped
                for exercise_name, exercise_sets in exercises_by_name.items():
                    report.append(f"**{exercise_name}** ({len(exercise_sets)} sets)")
                    report.append("| Set | Reps | Weight | Type |")
                    report.append("|-----|------|---------|------|")
                    
                    for i, set_info in enumerate(exercise_sets, 1):
                        report.append(f"| {i} | {set_info['reps']} | "
                                    f"{set_info['weight']:.1f} {set_info['weight_unit']} | "
                                    f"{'Warmup' if set_info['is_warmup'] else 'Working'} |")
                    report.append("")
            
            # Exercise Details
            report.append("### Exercise Details\n")
            for exercise, details in sorted(summary['Exercise_details'].items()):
                report.append(f"#### {exercise}")
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
                
                # Sort sets chronologically (assuming they're already in order in the list)
                for i, set_info in enumerate(details['sets'], 1):
                    report.append(f"| {i} | {set_info['weight']:.1f} {weight_unit} | "
                                f"{set_info['reps']} | "
                                f"{'Warmup' if set_info['is_warmup'] else 'Working'} |")
                report.append("")
        else:
            # Summary report with just the key metrics
            if summary['Distance_by_exercise']:
                report.append("### Distance by Exercise")
                for exercise, distance in summary['Distance_by_exercise'].items():
                    report.append(f"- {exercise}: {distance:.2f} {distance_unit}")
                report.append("")
            
            if summary['Volume_by_exercise']:
                report.append("### Volume by Exercise")
                for exercise, volume in summary['Volume_by_exercise'].items():
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
    
    return "\n".join(report) 
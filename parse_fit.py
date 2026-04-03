#!/usr/bin/env python3
"""Parse FIT file and extract exercise summary from COROS export."""

import sys
import struct
from datetime import datetime, timedelta

def parse_fit_file(file_path):
    """Basic FIT parser to extract key summary information."""

    with open(file_path, 'rb') as f:
        data = f.read()

    # FIT header
    header_size = data[0]
    protocol_version = data[1]
    profile_version = struct.unpack('<H', data[2:4])[0]
    data_size = struct.unpack('<I', data[4:8])[0]
    data_crc = struct.unpack('<H', data[8:10])[0]

    print(f"File Header:")
    print(f"  Protocol Version: {protocol_version}.{protocol_version >> 4}")
    print(f"  Profile Version: {profile_version}")
    print(f"  Data Size: {data_size} bytes")
    print()

    # Parse records
    offset = header_size
    end_offset = header_size + data_size

    # Track summary data
    activity_type = None
    start_time = None
    total_distance = 0
    total_timer_time = 0
    total_elapsed_time = 0
    total_calories = 0
    avg_heart_rate = 0
    max_heart_rate = 0
    avg_speed = 0
    max_speed = 0
    total_ascent = 0
    total_descent = 0
    position_lat = None
    position_long = None
    sport = None
    num_records = 0

    sport_names = {
        0: 'Generic', 1: 'Running', 2: 'Cycling', 3: 'Swimming',
        4: 'Strength Training', 5: 'Hiking', 6: 'Walking', 7: 'Cycling (indoor',
        8: 'Swimming (open water)', 9: 'Swimrun', 10: 'Trail Running',
        11: 'Snowboarding', 12: 'Cross Country Skiing',
        13: 'Alpine Skiing', 14: 'Rowing', 15: 'Mountaineering',
    }

    while offset < end_offset:
        if offset + 1 > len(data):
            break
        header = data[offset]
        reserved = data[offset]
        compressed = (header & 0x80) != 0

        if compressed:
            # Compressed timestamp
            offset += 1
            continue
        else:
            # Normal header
            if offset + 3 > len(data):
                break
            arch = (data[offset+1] & 0x0F)
            mesg_num = struct.unpack('<H', data[offset+1:offset+3])[0] >> 4
            mesg_size = data[offset+2]
            offset += 3

            if mesg_num == 216:  # file_id
                pass
            elif mesg_num == 13:  # sport
                if offset + 1 < len(data):
                    sport = data[offset]
                    if sport in sport_names:
                        sport = sport_names[sport]
            elif mesg_num == 34:  # session
                # Session has summary data
                # Try to read fields
                session_offset = offset
                for i in range(0, mesg_size, 2):
                    if session_offset + i + 2 <= len(data):
                        # Very basic - distance is at 0x86 field 13, 13 is distance, 14 is timer time, 15 is elapsed time
                        pass
            elif mesg_num == 48:  # activity
                pass
                # Get activity
            num_records += 1
            offset += mesg_size

    print("Extracting summary...")
    print()

    # Try a more reliable approach with existing library if available
    try:
        from fitparse import FitFile

        print("Using fitparse library for full parsing...")
        print()
        fitfile = FitFile(open(file_path, 'rb'))

        # Get data messages
        sessions = list(fitfile.get_messages('session'))
        for session in sessions:
            print("Session Summary:")
            fields = {}
            for field in session.fields:
                if field.value is not None and field.value != '':
                    fields[field.name] = field.value

            if 'start_time' in fields:
                start_time = fields['start_time']
                # Convert UTC to Beijing time (UTC+8)
                from datetime import timedelta
                start_time_bj = start_time + timedelta(hours=8)
                print(f"  Start Time (UTC): {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  Start Time (北京): {start_time_bj.strftime('%Y-%m-%d %H:%M:%S')}")

            if 'total_distance' in fields:
                dist_km = fields['total_distance'] / 1000.0
                print(f"  Distance: {dist_km:.2f} km")

            if 'total_timer_time' in fields:
                # FIT total_timer_time is already in seconds for most profiles
                seconds = fields['total_timer_time']
                if seconds > 100000:  # if it's in milliseconds
                    seconds = seconds / 1000.0
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                if hours > 0:
                    print(f"  Moving Time: {hours}h {minutes}m {secs}s")
                else:
                    print(f"  Moving Time: {minutes}m {secs}s")

            if 'total_calories' in fields:
                print(f"  Calories: {fields['total_calories']} kcal")

            if 'avg_heart_rate' in fields:
                print(f"  Avg Heart Rate: {fields['avg_heart_rate']} bpm")

            if 'max_heart_rate' in fields:
                print(f"  Max Heart Rate: {fields['max_heart_rate']} bpm")

            if 'avg_speed' in fields:
                # speed is m/s, convert to km/h
                if fields['avg_speed'] > 0:
                    kmh = fields['avg_speed'] * 3.6
                    if fields.get('sport', 0) in [1, 5, 6, 10]:  # running/walking/hiking running
                        pace_min_km = (1000.0 / (fields['avg_speed'] * 60))
                        min_per_km = int(pace_min_km)
                        sec_per_km = int((pace_min_km - min_per_km) * 60)
                        print(f"  Avg Pace: {min_per_km}'{sec_per_km:02d}\"/km")
                    else:
                        print(f"  Avg Speed: {kmh:.1f} km/h")

            if 'total_ascent' in fields and fields['total_ascent'] > 0:
                print(f"  Total Ascent: {fields['total_ascent']} m")

            if 'total_descent' in fields and fields['total_descent'] > 0:
                print(f"  Total Descent: {fields['total_descent']} m")
            print()

        # Get activity type
        sport_names = {
            0: 'Generic', 1: 'Running', 2: 'Cycling', 3: 'Swimming',
            4: 'Strength Training', 5: 'Hiking', 6: 'Walking', 7: 'Cycling (indoor)',
            8: 'Swimming (open water)', 9: 'Swimrun', 10: 'Trail Running',
            11: 'Snowboarding', 12: 'Cross Country Skiing',
            13: 'Alpine Skiing', 14: 'Rowing', 15: 'Mountaineering',
            16: 'Yoga', 17: 'Pilates', 18: 'Elliptical', 19: 'Stair Climbing',
            20: 'Cross Training', 21: 'Bench Press', 22: 'Crunches',
            23: 'Plank', 24: 'Lunges', 25: 'Pushups', 26: 'Pullups',
            27: 'Weights', 28: 'HIIT', 29: 'Yoga', 30: 'Paddle',
            31: 'Kayaking', 32: 'Rowing', 33: 'SUP', 34: 'Surfing',
            35: 'KiteSurfing', 36: 'Windsurfing',
        }

        # Get activity type
        sports = list(fitfile.get_messages('sport'))
        for sport_msg in sports:
            for field in sport_msg.fields:
                if field.name == 'sport' and field.value is not None:
                    sport = field.value
                    break

        if sport is not None:
            if isinstance(sport, int) and sport in sport_names:
                sport_name = sport_names[sport]
            else:
                sport_name = str(sport).capitalize()
            print(f"  Sport/Activity Type: {sport_name}")
            print()

    except ImportError:
        print("Note: fitparse library not installed. Install it with:")
        print("    pip install fitparse")
        print()

        # Try manual extraction not implemented in basic mode...")
        print("Basic info found in this script requires fitparse library for accurate parsing.")

    return True

if __name__ == '__main__':
    if len(sys.argv) > 1:
        parse_fit_file(sys.argv[1])
    else:
        parse_fit_file('476407660602753025.fit')

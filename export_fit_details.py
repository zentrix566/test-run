#!/usr/bin/env python3
"""Extract detailed record data from FIT file."""

import sys
from fitparse import FitFile

def export_details(file_path):
    """Export detailed information from FIT file."""

    print("=" * 60)
    print("Detailed FIT File Contents")
    print("=" * 60)
    print()

    fitfile = FitFile(open(file_path, 'rb'))

    # Count message types
    msg_counts = {}
    for msg in fitfile.get_messages():
        msg_type = msg.name
        msg_counts[msg_type] = msg_counts.get(msg_type, 0) + 1

    print("Message types found in file:")
    for msg_type, count in sorted(msg_counts.items()):
        print(f"  {msg_type}: {count} records")
    print()

    print("=" * 60)
    print()

    # Show sample record data (first 10 GPS records)
    print("Sample GPS track points (first 10):")
    print()
    print(f"{'Index':<5} {'Latitude':<12} {'Longitude':<12} {'Altitude':<10} {'Heart Rate':<10} {'Speed':<8}")
    print("-" * 60)

    count = 0
    for record in fitfile.get_messages('record'):
        if count >= 10:
            break

        # Get fields
        lat = record.get_value('position_lat')
        lon = record.get_value('position_long')
        alt = record.get_value('altitude')
        hr = record.get_value('heart_rate')
        speed = record.get_value('speed')

        # Convert semicircles to degrees
        if lat is not None:
            lat = lat * (180.0 / 2147483648)
        if lon is not None:
            lon = lon * (180.0 / 2147483648)
        if speed is not None:
            speed = speed * 3.6  # m/s to km/h

        lat_str = f"{lat:.6f}" if lat is not None else "-"
        lon_str = f"{lon:.6f}" if lon is not None else "-"
        alt_str = f"{alt:.1f} m" if alt is not None else "-"
        hr_str = f"{hr} bpm" if hr is not None else "-"
        speed_str = f"{speed:.1f}" if speed is not None else "-"

        print(f" {count+1:<4} {lat_str:<12} {lon_str:<12} {alt_str:<10} {hr_str:<10} {speed_str:<8}")
        count += 1

    print()
    print(f"... Total {msg_counts.get('record', 0)} GPS track points")
    print()

    # Export all data to CSV for easy viewing
    csv_path = 'fit_export.csv'
    print(f"Exporting all track points to {csv_path}...")

    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write('index,timestamp,latitude_deg,longitude_deg,altitude_m,heart_rate_bpm,speed_kmh\n')

        for i, record in enumerate(fitfile.get_messages('record')):
            lat = record.get_value('position_lat')
            lon = record.get_value('position_long')
            alt = record.get_value('altitude')
            hr = record.get_value('heart_rate')
            speed = record.get_value('speed')
            ts = record.get_value('timestamp')

            if lat is not None:
                lat = lat * (180.0 / 2147483648)
            if lon is not None:
                lon = lon * (180.0 / 2147483648)
            if speed is not None:
                speed = speed * 3.6

            f.write(f"{i},{ts},{lat},{lon},{alt},{hr},{speed}\n")

    print(f"   Done! Exported {msg_counts.get('record', 0)} points to {csv_path}")
    print()

    # Also show session data with all fields
    print("Full session data fields:")
    print()
    sessions = list(fitfile.get_messages('session'))
    for session in sessions:
        for field in session.fields:
            if field.value is not None:
                print(f"  {field.name:<20} = {field.value}")

    return True

if __name__ == '__main__':
    if len(sys.argv) > 1:
        export_details(sys.argv[1])
    else:
        export_details('476407660602753025.fit')

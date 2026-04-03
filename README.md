# test-run

Personal test repository for experimenting and testing various code snippets, concepts, and projects.

## COROS FIT File Parser

Parse and extract data from COROS/ Garmin FIT format exported exercise files.

### Contents
- `476407660602753025.fit` - Original FIT file exported from COROS (42.4km run on 2026-03-28)
- `parse_fit.py` - Extract exercise summary from FIT file
- `export_fit_details.py` - Export all GPS track points to CSV
- `fit_export.csv` - Exported detailed GPS data (15,060 points) with coordinates, heart rate, speed

### Exercise Summary
| Metric | Value |
|--------|-------|
| **Sport** | Running |
| **Date** | 2026-03-28 |
| **Distance** | **42.40 km** |
| **Time** | 4h 10m 59s |
| **Calories** | 3745 kcal |
| **Avg Heart Rate** | 153 bpm |
| **Max Heart Rate** | 161 bpm |
| **Avg Pace** | 5'53"/km |
| **Total Ascent** | 47 m |
| **Total Descent** | 50 m |

### Usage
```bash
# Install dependency
pip install fitparse

# Extract summary
python parse_fit.py your_file.fit

# Export detailed GPS data to CSV
python export_fit_details.py your_file.fit
```

## License

MIT © [zentrix566](https://github.com/zentrix566)

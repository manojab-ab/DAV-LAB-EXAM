# ACT 2: Data Cleaning

## What I did
- Loaded the taxi data from `data/raw/sample_trips.csv`.
- If the file was missing, the script made a sample dataset.
- Checked which trips looked real and which looked wrong.

## How I checked trips
1. Must have pickup time, dropoff time, fare, distance, and passenger count.
2. No exact duplicate trips.
3. Pickup time must be before dropoff time.
4. No weird values like negative distance or huge fare.
5. Location IDs must be in valid NYC range.

## What I got
- Clean trips saved to `data/processed/cleaned_trips.csv`.
- A summary of how many records stayed and why some were removed.

## Notes
This act is about trust. Only good-looking trips are kept for the next steps.

# ACT 6: Power BI Guide

## What to use
- Load `data/processed/cleaned_trips.csv` as your main data.
- If you want, also load `data/raw/sample_trips.csv` to compare.

## What to show
1. **Trust the data**
   - Show raw count vs cleaned count.
   - Show why records were removed: missing fields, duplicates, bad times, outliers, bad locations.
   - Use a bar chart for the removal reasons.

2. **What the data actually says**
   - Use only cleaned data.
   - Show trip volume by hour and by day.
   - Show average fare and average distance.
   - Use line charts or heatmaps.

3. **Where the system is under pressure**
   - Point out hours or days that look weird.
   - Compare stable times and noisy times.
   - Use a KPI or highlight cards.

4. **What changes if policy shifts**
   - Show the fare-change scenario and the volume-change scenario.
   - Use side-by-side bars.
   - Make it clear this is a range, not a perfect prediction.

5. **How you can be wrong**
   - Show one wrong story from the same data.
   - Then show the corrected version using cleaned data.
   - This is the “don’t jump to conclusions” section.

## How to build it
1. Open Power BI Desktop.
2. Click "Get data" → "Text/CSV" and load `data/processed/cleaned_trips.csv`.
3. Check data types in Power Query.
4. Build these visuals:
   - Card: Raw count vs cleaned count.
   - Bar chart: why records were removed.
   - Line chart: trip volume by hour.
   - Line chart: average fare by hour.
   - Heatmap or matrix: trip volume by day of week and hour.
   - Bar chart: baseline vs scenario revenue.
5. Add small text notes that explain each page.

## Notes
This is the only part you need to make in Power BI. The rest of the work is already done in the cleaned data and the act notes.

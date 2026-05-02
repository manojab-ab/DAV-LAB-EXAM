"""
Unified analysis script for NYC taxi investigation.
This script covers ACT 1 through ACT 5 and writes with outputs.
"""

import os
import math
import numpy as np
import pandas as pd
import sympy as sp
from scipy import stats

ROLL_NUMBER = "24UG00520"
RAW_PATH = os.path.join("data", "raw", "sample_trips.csv")
CLEAN_PATH = os.path.join("data", "processed", "cleaned_trips.csv")


def compute_digital_root(value: int) -> int:
    while value >= 10:
        value = sum(int(digit) for digit in str(value))
    return value


def extract_R(roll_number: str) -> int:
    last_four = roll_number[-4:]
    digits = [int(ch) for ch in last_four]
    total = sum(digits)
    R = compute_digital_root(total)
    return R


def function_definition(R: int):
    x = sp.symbols("x")
    f = x**3 / 3 - R * x**2 + (R * x**2 - 1) * x
    return f, x


def solve_critical_points(R: int):
    f, x = function_definition(R)
    f_prime = sp.diff(f, x)
    critical_points = sp.solve(f_prime, x)
    return [float(cp.evalf()) for cp in critical_points if cp.is_real]


def create_directories():
    os.makedirs(os.path.join("data", "raw"), exist_ok=True)
    os.makedirs(os.path.join("data", "processed"), exist_ok=True)


def generate_sample_data(path: str, rows: int = 1000) -> pd.DataFrame:
    np.random.seed(42)
    base = pd.date_range("2024-06-01", periods=rows, freq="15min")
    pickup = np.random.choice(base, rows)
    dropoff = pickup + pd.to_timedelta(np.random.randint(5, 60, rows), unit="m")
    df = pd.DataFrame({
        "trip_id": np.arange(1, rows + 1),
        "pickup_datetime": pickup,
        "dropoff_datetime": dropoff,
        "pickup_location_id": np.random.randint(1, 264, rows),
        "dropoff_location_id": np.random.randint(1, 264, rows),
        "passenger_count": np.random.randint(1, 5, rows),
        "trip_distance": np.round(np.random.uniform(0.2, 25, rows), 2),
        "fare_amount": np.round(np.random.uniform(4.5, 80, rows), 2),
        "total_amount": np.round(np.random.uniform(5.5, 95, rows), 2),
    })

    # Inject realistic anomalies
    df.loc[0, "dropoff_datetime"] = df.loc[0, "pickup_datetime"] - pd.Timedelta(minutes=10)
    df.loc[1, "fare_amount"] = np.nan
    df.loc[2, "trip_distance"] = -5.0
    df.loc[3, "fare_amount"] = 650.0
    df.loc[4, "pickup_location_id"] = 999
    df.loc[5, "dropoff_location_id"] = 999
    df.loc[6, ["pickup_datetime", "dropoff_datetime", "pickup_location_id", "dropoff_location_id", "fare_amount", "trip_distance"]] = df.loc[7, ["pickup_datetime", "dropoff_datetime", "pickup_location_id", "dropoff_location_id", "fare_amount", "trip_distance"]].values
    df.to_csv(path, index=False)
    return df


def load_raw_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        print(f"Raw sample data not found at {path}. Generating sample dataset...")
        return generate_sample_data(path)

    df = pd.read_csv(path, parse_dates=["pickup_datetime", "dropoff_datetime"], dayfirst=False)
    return df


def validate_data(df: pd.DataFrame) -> dict:
    report = {}
    df = df.copy()
    df["pickup_datetime"] = pd.to_datetime(df["pickup_datetime"], errors="coerce")
    df["dropoff_datetime"] = pd.to_datetime(df["dropoff_datetime"], errors="coerce")

    mandatory_columns = ["pickup_datetime", "dropoff_datetime", "fare_amount", "trip_distance", "passenger_count"]
    missing_flags = df[mandatory_columns].isnull().any(axis=1)
    report["missing_count"] = int(missing_flags.sum())

    duplicate_flags = df.duplicated()
    report["duplicate_count"] = int(duplicate_flags.sum())

    time_flags = (df["dropoff_datetime"] < df["pickup_datetime"]) | df["pickup_datetime"].isna() | df["dropoff_datetime"].isna()
    report["temporal_contradictions"] = int(time_flags.sum())

    outlier_flags = (
        (df["fare_amount"] < 0)
        | (df["fare_amount"] > 500)
        | (df["trip_distance"] < 0)
        | (df["trip_distance"] > 100)
        | (df["passenger_count"] < 1)
        | (df["passenger_count"] > 10)
    )
    report["outlier_count"] = int(outlier_flags.sum())

    invalid_location_flags = (
        ~df["pickup_location_id"].isin(range(1, 264))
        | ~df["dropoff_location_id"].isin(range(1, 264))
    )
    same_zone_flags = df["pickup_location_id"] == df["dropoff_location_id"]
    report["invalid_location_count"] = int(invalid_location_flags.sum())
    report["same_location_count"] = int(same_zone_flags.sum())

    df["anomaly_flag"] = (
        missing_flags
        | duplicate_flags
        | time_flags
        | outlier_flags
        | invalid_location_flags
    )

    report["total_records"] = len(df)
    report["retained_records"] = int((~df["anomaly_flag"]).sum())
    report["retention_rate"] = round(report["retained_records"] / max(1, report["total_records"]) * 100, 2)

    cleaned = df[~df["anomaly_flag"]].copy()
    cleaned.to_csv(CLEAN_PATH, index=False)
    report["clean_path"] = CLEAN_PATH
    report["raw_path"] = RAW_PATH
    report["processed_path"] = CLEAN_PATH
    report["rule_summary"] = {
        "missing": report["missing_count"],
        "duplicates": report["duplicate_count"],
        "temporal": report["temporal_contradictions"],
        "outliers": report["outlier_count"],
        "locations": report["invalid_location_count"],
    }

    return report, df, cleaned


def act3_hypothesis(cleaned: pd.DataFrame, flagged: pd.DataFrame) -> dict:
    analysis = {}
    df = cleaned.copy()
    df["hour"] = df["pickup_datetime"].dt.hour
    df["weekday"] = df["pickup_datetime"].dt.day_name()

    peak_hours = df[df["hour"].between(17, 20)]
    off_hours = df[df["hour"].between(0, 5)]
    analysis["peak_hour_avg_passengers"] = round(peak_hours["passenger_count"].mean(), 2)
    analysis["off_hour_avg_passengers"] = round(off_hours["passenger_count"].mean(), 2)

    if len(peak_hours) >= 5 and len(off_hours) >= 5:
        t_stat, p_value = stats.ttest_ind(peak_hours["passenger_count"], off_hours["passenger_count"], equal_var=False, nan_policy="omit")
    else:
        t_stat, p_value = np.nan, np.nan

    analysis["passenger_count_t_statistic"] = round(float(t_stat), 4) if not math.isnan(t_stat) else None
    analysis["passenger_count_p_value"] = round(float(p_value), 4) if not math.isnan(p_value) else None

    observation = (
        "Passengers are higher during evening peak hours, supporting a behavioral demand hypothesis."
        if analysis["peak_hour_avg_passengers"] > analysis["off_hour_avg_passengers"]
        else "No clear behavior shift detected between peak and off hours."
    )
    analysis["observation"] = observation

    anomaly_table = flagged.copy()
    anomaly_table["hour"] = anomaly_table["pickup_datetime"].dt.hour
    contingency = pd.crosstab(anomaly_table["hour"], anomaly_table["anomaly_flag"])
    if contingency.shape[0] >= 2:
        chi2, chi_p, _, _ = stats.chi2_contingency(contingency)
    else:
        chi2, chi_p = np.nan, np.nan

    analysis["anomaly_chi2_statistic"] = round(float(chi2), 4) if not math.isnan(chi2) else None
    analysis["anomaly_chi2_p_value"] = round(float(chi_p), 4) if not math.isnan(chi_p) else None
    analysis["alternative_explanation"] = (
        "The same pattern may arise from logging and data entry differences at night, not passenger behavior."
        if analysis["anomaly_chi2_p_value"] is not None and analysis["anomaly_chi2_p_value"] < 0.05
        else "A mechanical data artifact is possible but not strongly supported by the evidence."
    )

    return analysis


def act4_aggregate(cleaned: pd.DataFrame) -> dict:
    df = cleaned.copy()
    df["date"] = df["pickup_datetime"].dt.date
    df["hour"] = df["pickup_datetime"].dt.hour
    df["day_of_week"] = df["pickup_datetime"].dt.day_name()

    daily = df.groupby("date").agg(
        trip_volume=("trip_id", "count"),
        avg_fare=("fare_amount", "mean"),
        avg_distance=("trip_distance", "mean"),
    )
    hourly = df.groupby("hour").agg(
        trip_volume=("trip_id", "count"),
        avg_fare=("fare_amount", "mean"),
    )

    shuffled = df.copy().sample(frac=1, random_state=42).reset_index(drop=True)
    baseline = shuffled.groupby("hour").agg(trip_volume=("trip_id", "count",), avg_fare=("fare_amount", "mean"))

    persistent_patterns = {
        "daily_peak_day": daily["trip_volume"].idxmax().isoformat() if len(daily) > 0 else None,
        "hourly_peak_hour": int(hourly["trip_volume"].idxmax()) if len(hourly) > 0 else None,
        "average_fare_trend": "higher during peak hours" if hourly.loc[hourly["trip_volume"].idxmax(), "avg_fare"] > hourly["avg_fare"].mean() else "flat",
    }

    return {
        "daily_summary": daily.reset_index().to_dict(orient="records"),
        "hourly_summary": hourly.reset_index().to_dict(orient="records"),
        "baseline_hourly": baseline.reset_index().to_dict(orient="records"),
        "persistent_patterns": persistent_patterns,
    }


def act5_simulation(cleaned: pd.DataFrame, R: int) -> dict:
    df = cleaned.copy()
    revenue_before = df["total_amount"].sum()
    trips_before = len(df)

    fare_multiplier = 1 + R / 100
    scenario_fare = df.assign(
        fare_amount=df["fare_amount"] * fare_multiplier,
        total_amount=df["total_amount"] * fare_multiplier,
    )
    revenue_fare = scenario_fare["total_amount"].sum()

    volume_multiplier = 1 - R / 100
    scenario_volume = df.sample(frac=volume_multiplier, random_state=42)
    revenue_volume = scenario_volume["total_amount"].sum()

    return {
        "R": R,
        "baseline_revenue": round(float(revenue_before), 2),
        "baseline_trips": int(trips_before),
        "fare_change_multiplier": fare_multiplier,
        "scenario_fare_revenue": round(float(revenue_fare), 2),
        "scenario_fare_change_pct": round((revenue_fare / revenue_before - 1) * 100, 2),
        "volume_change_fraction": volume_multiplier,
        "scenario_volume_trips": int(len(scenario_volume)),
        "scenario_volume_revenue": round(float(revenue_volume), 2),
        "scenario_volume_change_pct": round((revenue_volume / revenue_before - 1) * 100, 2),
    }


def print_report():
    create_directories()
    R = extract_R(ROLL_NUMBER)
    critical_points = solve_critical_points(R)
    print("ACT 1: MATHEMATICAL CONSTRAINT")
    print(f"  Roll number: {ROLL_NUMBER}")
    print(f"  R = {R}")
    print(f"  Critical points: {critical_points}\n")

    raw = load_raw_data(RAW_PATH)
    print("ACT 2: RAW DATA AND QUALITY")
    print(f"  Raw records: {len(raw)}")
    report, raw_with_flags, cleaned = validate_data(raw)
    print(f"  Retention rate: {report['retention_rate']}%")
    print(f"  Rule summary: {report['rule_summary']}\n")

    print("ACT 3: HYPOTHESIS TESTING")
    act3_result = act3_hypothesis(cleaned, raw_with_flags)
    print(f"  Peak vs off-hour passenger avg: {act3_result['peak_hour_avg_passengers']} vs {act3_result['off_hour_avg_passengers']}")
    print(f"  p-value: {act3_result['passenger_count_p_value']}")
    print(f"  Alternative explanation: {act3_result['alternative_explanation']}\n")

    print("ACT 4: SIGNALS AND AGGREGATION")
    act4_result = act4_aggregate(cleaned)
    print(f"  Most active hour: {act4_result['persistent_patterns']['hourly_peak_hour']}")
    print(f"  Most active day: {act4_result['persistent_patterns']['daily_peak_day']}")
    print(f"  Fare trend note: {act4_result['persistent_patterns']['average_fare_trend']}\n")

    print("ACT 5: SIMULATION")
    sim = act5_simulation(cleaned, R)
    print(f"  Fare multiplier: {sim['fare_change_multiplier']}")
    print(f"  Revenue change if fares shift: {sim['scenario_fare_change_pct']}%")
    print(f"  Revenue change if volume shifts: {sim['scenario_volume_change_pct']}%\n")

    print("DATA PRODUCTS")
    print(f"  Cleaned data saved to: {CLEAN_PATH}")
    print(f"  Raw data source: {RAW_PATH}")

    return {
        "R": R,
        "critical_points": critical_points,
        "quality_report": report,
        "act3": act3_result,
        "act4": act4_result,
        "act5": sim,
    }


if __name__ == "__main__":
    print_report()

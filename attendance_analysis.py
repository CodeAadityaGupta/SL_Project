"""
Smart Attendance Management and Analysis using NumPy and Pandas
Module: attendance_analysis.py
Author: Aaditya Gupta & AI Assistant

Functionalities:
1. Data cleaning & preprocessing using Pandas
2. Attendance percentage calculation per student using NumPy & Pandas
3. Low-attendance detection (< 75% threshold) with recovery shortfall using NumPy
4. Statistical distribution analysis using NumPy (mean, median, std dev, min, max, percentiles)
5. Date-wise and Day-of-Week trend analysis with linear regression slope using NumPy & Pandas
6. Formatted ASCII dashboard, interactive menu, and CSV export
"""

import os
import numpy as np
import pandas as pd


def load_and_clean_data(csv_path="attendance_records.csv"):
    """
    Loads and cleans attendance records from CSV.
    Handles missing values, standardizes casing, and creates numeric flags.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found at {csv_path}")

    df = pd.read_csv(csv_path)

    # Standardize column names
    df.columns = [col.strip() for col in df.columns]

    # Clean text columns
    df['ATTENDANCE'] = df['ATTENDANCE'].astype(str).str.strip().str.lower()
    df['NAME'] = df['NAME'].astype(str).str.strip().str.title()

    # Filter only valid attendance entries
    df = df[df['ATTENDANCE'].isin(['present', 'absent'])].copy()

    # Parse and clean dates
    df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
    df = df.dropna(subset=['DATE']).copy()

    # Vectorized binary attendance using NumPy (1 for present, 0 for absent)
    df['Is_Present'] = np.where(df['ATTENDANCE'] == 'present', 1, 0)

    return df


def calculate_student_summary(df):
    """
    Calculates total classes, attended, absent, attendance percentage,
    and eligibility status per student using NumPy and Pandas.
    """
    # Group by student name with Roll Number
    summary = df.groupby('NAME').agg(
        Roll_No=('ROLLno', 'min'),
        Total_Classes=('Is_Present', 'count'),
        Attended=('Is_Present', 'sum')
    ).reset_index()

    # Calculate Absent count
    summary['Absent'] = summary['Total_Classes'] - summary['Attended']

    # Vectorized percentage calculation with NumPy
    total_arr = summary['Total_Classes'].to_numpy()
    attended_arr = summary['Attended'].to_numpy()
    pct_arr = np.round((attended_arr / np.maximum(total_arr, 1)) * 100, 2)
    summary['Percentage'] = pct_arr

    # Status classification using NumPy np.select
    conditions = [
        pct_arr >= 75.0,
        (pct_arr >= 60.0) & (pct_arr < 75.0),
        pct_arr < 60.0
    ]
    choices = ['Eligible (>=75%)', 'Warning (60-74%)', 'Defaulter / Critical (<60%)']
    summary['Status'] = np.select(conditions, choices, default='Unknown')

    # Sort by Roll Number
    summary = summary.sort_values(by=['Roll_No', 'NAME']).reset_index(drop=True)
    return summary


def detect_low_attendance(summary_df, threshold=75.0):
    """
    Detects students below the specified attendance threshold (defaulters)
    and computes the minimum consecutive classes needed to reach the threshold using NumPy.
    """
    total_arr = summary_df['Total_Classes'].to_numpy()
    attended_arr = summary_df['Attended'].to_numpy()
    pct_arr = summary_df['Percentage'].to_numpy()

    # Boolean mask for low attendance using NumPy
    defaulter_mask = pct_arr < threshold
    defaulters = summary_df[defaulter_mask].copy()

    if len(defaulters) > 0:
        d_tot = total_arr[defaulter_mask]
        d_att = attended_arr[defaulter_mask]
        # Formula for consecutive classes needed (x) to achieve threshold T:
        # (Attended + x) / (Total + x) >= T/100
        # x >= (T/100 * Total - Attended) / (1 - T/100)
        t_factor = threshold / 100.0
        classes_needed = np.maximum(
            0,
            np.ceil((t_factor * d_tot - d_att) / (1.0 - t_factor))
        ).astype(int)
        defaulters['Classes_Needed_For_75'] = classes_needed
    else:
        defaulters['Classes_Needed_For_75'] = []

    return defaulters.sort_values(by='Percentage').reset_index(drop=True)


def compute_numpy_statistics(summary_df):
    """
    Computes class-wide statistical insights using NumPy mathematical functions.
    """
    pct_arr = summary_df['Percentage'].to_numpy()
    total_classes = summary_df['Total_Classes'].to_numpy()

    stats = {
        'total_students': len(summary_df),
        'mean_attendance': float(np.round(np.mean(pct_arr), 2)),
        'median_attendance': float(np.round(np.median(pct_arr), 2)),
        'std_deviation': float(np.round(np.std(pct_arr), 2)),
        'min_attendance': float(np.min(pct_arr)),
        'max_attendance': float(np.max(pct_arr)),
        'iqr_25': float(np.round(np.percentile(pct_arr, 25), 2)),
        'iqr_75': float(np.round(np.percentile(pct_arr, 75), 2)),
        'highest_students': summary_df[pct_arr == np.max(pct_arr)][['Roll_No', 'NAME', 'Percentage']].to_dict('records'),
        'lowest_students': summary_df[pct_arr == np.min(pct_arr)][['Roll_No', 'NAME', 'Percentage']].to_dict('records'),
        'count_excellent': int(np.sum(pct_arr >= 85.0)),
        'count_eligible': int(np.sum((pct_arr >= 75.0) & (pct_arr < 85.0))),
        'count_warning': int(np.sum((pct_arr >= 60.0) & (pct_arr < 75.0))),
        'count_critical': int(np.sum(pct_arr < 60.0))
    }
    return stats


def analyze_attendance_trends(df):
    """
    Performs date-wise and day-of-week attendance trend analysis.
    Uses NumPy polyfit to estimate overall trajectory slope.
    """
    # Date-wise aggregation
    daily = df.groupby(df['DATE'].dt.date).agg(
        Total=('Is_Present', 'count'),
        Present=('Is_Present', 'sum')
    ).reset_index()
    daily['Absent'] = daily['Total'] - daily['Present']

    # Vectorized percentage computation using NumPy
    present_arr = daily['Present'].to_numpy()
    total_arr = daily['Total'].to_numpy()
    daily_pct = np.round((present_arr / np.maximum(total_arr, 1)) * 100, 2)
    daily['Attendance_Pct'] = daily_pct

    # Linear regression slope on daily attendance using NumPy
    if len(daily) > 1:
        x = np.arange(len(daily))
        slope, intercept = np.polyfit(x, daily_pct, 1)
        if slope > 0.15:
            trajectory = "Improving (+)"
        elif slope < -0.15:
            trajectory = "Declining (-)"
        else:
            trajectory = "Stable (~)"
    else:
        slope = 0.0
        trajectory = "Insufficient data"

    # Day of week patterns
    df_copy = df.copy()
    df_copy['Day_Name'] = df_copy['DATE'].dt.day_name()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_summary = df_copy.groupby('Day_Name').agg(
        Total=('Is_Present', 'count'),
        Present=('Is_Present', 'sum')
    ).reindex(day_order).dropna()
    day_pres = day_summary['Present'].to_numpy()
    day_tot = day_summary['Total'].to_numpy()
    day_summary['Pct'] = np.round((day_pres / np.maximum(day_tot, 1)) * 100, 2)

    return {
        'daily_df': daily,
        'slope': float(np.round(slope, 3)),
        'trajectory': trajectory,
        'day_summary': day_summary,
        'best_day': daily.loc[daily['Attendance_Pct'].idxmax()][['DATE', 'Attendance_Pct']].to_dict(),
        'lowest_day': daily.loc[daily['Attendance_Pct'].idxmin()][['DATE', 'Attendance_Pct']].to_dict()
    }


def make_progress_bar(pct, width=10):
    """Creates a Windows-safe visual ASCII progress bar for attendance percentage."""
    filled = int(round((pct / 100.0) * width))
    bar = "=" * filled + "-" * (width - filled)
    return f"[{bar}]"


def print_dashboard(summary_df, defaulters_df, stats, trends):
    """Prints a structured executive dashboard in the console."""
    border = "=" * 85
    print("\n" + border)
    print("      SMART ATTENDANCE MANAGEMENT & ANALYSIS (NumPy & Pandas)")
    print(border)

    # 1. Class Statistics Overview
    print("\n--- 1. CLASS STATISTICAL OVERVIEW (NumPy Insights) ---")
    print(f"  * Total Students Evaluated   : {stats['total_students']}")
    print(f"  * Class Average Attendance   : {stats['mean_attendance']}%")
    print(f"  * Median Attendance          : {stats['median_attendance']}%")
    print(f"  * Standard Deviation (Spread): {stats['std_deviation']}%")
    print(f"  * IQR (25th to 75th %ile)    : {stats['iqr_25']}% - {stats['iqr_75']}%")
    print(f"  * Overall Trend Trajectory   : {trends['trajectory']} (Slope: {trends['slope']})")
    print(f"  * Attendance Breakdown       : Excellent(>=85%): {stats['count_excellent']} | "
          f"Eligible(75-84%): {stats['count_eligible']} | "
          f"Warning(60-74%): {stats['count_warning']} | "
          f"Defaulter(<60%): {stats['count_critical']}")

    # 2. Student Attendance Summary Table
    print("\n--- 2. STUDENT-WISE ATTENDANCE & PERCENTAGES ---")
    header = f"{'Roll':<6}{'Student Name':<24}{'Total':<8}{'Present':<9}{'Absent':<8}{'Pct %':<9}{'Progress':<14}{'Status'}"
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    for _, row in summary_df.iterrows():
        pbar = make_progress_bar(row['Percentage'])
        print(f"{int(row['Roll_No']):<6}{row['NAME']:<24}{int(row['Total_Classes']):<8}{int(row['Attended']):<9}"
              f"{int(row['Absent']):<8}{row['Percentage']:<9.2f}{pbar:<14}{row['Status']}")
    print("-" * len(header))

    # 3. Defaulter / Low Attendance Detection Alert
    print("\n--- 3. LOW-ATTENDANCE DETECTION ALERT (< 75% Requirement) ---")
    if len(defaulters_df) == 0:
        print("  [OK] Excellent! All students satisfy the minimum 75% attendance criteria.")
    else:
        print(f"  [!] WARNING: {len(defaulters_df)} student(s) currently below the 75% required attendance threshold!")
        d_header = f"{'Roll':<6}{'Student Name':<24}{'Attended/Total':<16}{'Pct %':<10}{'Classes Needed For 75%'}"
        print("-" * len(d_header))
        print(d_header)
        print("-" * len(d_header))
        for _, row in defaulters_df.iterrows():
            ratio = f"{int(row['Attended'])} / {int(row['Total_Classes'])}"
            print(f"{int(row['Roll_No']):<6}{row['NAME']:<24}{ratio:<16}{row['Percentage']:<10.2f}{int(row['Classes_Needed_For_75'])} consecutive class(es)")
        print("-" * len(d_header))

    # 4. Day-of-Week Patterns & Recent Trends
    print("\n--- 4. ATTENDANCE TREND ANALYSIS ---")
    print(f"  * Best Attendance Date     : {trends['best_day']['DATE']} ({trends['best_day']['Attendance_Pct']}%)")
    print(f"  * Lowest Attendance Date   : {trends['lowest_day']['DATE']} ({trends['lowest_day']['Attendance_Pct']}%)")
    print("\n  Day-of-Week Attendance Pattern:")
    for day, row in trends['day_summary'].iterrows():
        print(f"    - {day:<10}: {row['Pct']:>6.2f}% ({int(row['Present'])} present out of {int(row['Total'])})")

    # Recent 5 Dates
    recent_daily = trends['daily_df'].tail(5)
    print("\n  Last 5 Recorded Sessions Trend:")
    for _, r in recent_daily.iterrows():
        pbar = make_progress_bar(r['Attendance_Pct'], width=8)
        print(f"    - {str(r['DATE']):<12}: {r['Attendance_Pct']:>6.2f}% {pbar} ({int(r['Present'])}/{int(r['Total'])})")

    print(border + "\n")


def export_analysis_report(summary_df, defaulters_df, output_path="attendance_analysis_report.csv"):
    """Exports full student summary report with defaulter analysis to a CSV file."""
    # Merge shortfall info into summary_df
    report = summary_df.copy()
    if 'Classes_Needed_For_75' in defaulters_df.columns and len(defaulters_df) > 0:
        needed_dict = dict(zip(defaulters_df['NAME'], defaulters_df['Classes_Needed_For_75']))
        report['Classes_Needed_For_75'] = report['NAME'].map(needed_dict).fillna(0).astype(int)
    else:
        report['Classes_Needed_For_75'] = 0

    report.to_csv(output_path, index=False)
    print(f"  [OK] Exported detailed analysis report to: {output_path}")


def search_student(summary_df, df, query):
    """Searches for a student by roll number or name and prints full history."""
    query = query.strip().lower()
    matches = summary_df[
        summary_df['NAME'].str.lower().str.contains(query) |
        (summary_df['Roll_No'].astype(str) == query)
    ]
    if matches.empty:
        print(f"No student matching '{query}' found.")
        return

    for _, row in matches.iterrows():
        print("\n" + "=" * 50)
        print(f" Student Report: {row['NAME']} (Roll No: {int(row['Roll_No'])})")
        print("=" * 50)
        print(f"  * Total Classes Conducted : {int(row['Total_Classes'])}")
        print(f"  * Classes Attended        : {int(row['Attended'])}")
        print(f"  * Classes Absent          : {int(row['Absent'])}")
        print(f"  * Attendance Percentage   : {row['Percentage']:.2f}%")
        print(f"  * Current Status          : {row['Status']}")
        if row['Percentage'] < 75.0:
            shortfall = int(np.maximum(0, np.ceil((0.75 * row['Total_Classes'] - row['Attended']) / 0.25)))
            print(f"  [!] Defaulter Alert: Must attend next {shortfall} classes consecutively to reach 75%.")
        else:
            print(f"  [OK] Eligible: Meets attendance criteria.")


def run_interactive_menu(csv_path="attendance_records.csv"):
    """
    Launches the interactive attendance analysis console.
    """
    try:
        df = load_and_clean_data(csv_path)
        summary = calculate_student_summary(df)
        defaulters = detect_low_attendance(summary)
        stats = compute_numpy_statistics(summary)
        trends = analyze_attendance_trends(df)
    except Exception as e:
        print(f"Error loading attendance dataset for analysis: {e}")
        return

    # Print dashboard once
    print_dashboard(summary, defaulters, stats, trends)

    # Automatically save report
    export_analysis_report(summary, defaulters)

    # Interactive Loop
    while True:
        print("\n" + "=" * 45)
        print("          ANALYSIS MENU OPTIONS")
        print("=" * 45)
        print(" [1] View Student Summary & Percentages")
        print(" [2] View Low-Attendance (< 75%) Defaulters Alert")
        print(" [3] View Class Statistics & NumPy Metrics")
        print(" [4] View Attendance Trends & Trajectory")
        print(" [5] Search Individual Student Details")
        print(" [6] Re-export Analysis Report (CSV)")
        print(" [7] Exit Analysis")
        print("=" * 45)

        try:
            choice = input("Enter your choice (1-7) or press Enter to exit: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting analysis.")
            break

        if choice == "1":
            header = f"{'Roll':<6}{'Student Name':<24}{'Total':<8}{'Present':<9}{'Absent':<8}{'Pct %':<9}{'Status'}"
            print("\n" + "-" * len(header))
            print(header)
            print("-" * len(header))
            for _, row in summary.iterrows():
                print(f"{int(row['Roll_No']):<6}{row['NAME']:<24}{int(row['Total_Classes']):<8}{int(row['Attended']):<9}{int(row['Absent']):<8}{row['Percentage']:<9.2f}{row['Status']}")
            print("-" * len(header))
        elif choice == "2":
            if len(defaulters) == 0:
                print("\n  ✓ No defaulters! All students have >= 75% attendance.")
            else:
                print(f"\n  ⚠️  LOW ATTENDANCE DEFAULTERS ({len(defaulters)} students below 75%):")
                d_header = f"{'Roll':<6}{'Student Name':<24}{'Attended/Total':<16}{'Pct %':<10}{'Classes Needed'}"
                print("-" * len(d_header))
                print(d_header)
                print("-" * len(d_header))
                for _, row in defaulters.iterrows():
                    ratio = f"{int(row['Attended'])} / {int(row['Total_Classes'])}"
                    print(f"{int(row['Roll_No']):<6}{row['NAME']:<24}{ratio:<16}{row['Percentage']:<10.2f}{int(row['Classes_Needed_For_75'])} class(es)")
                print("-" * len(d_header))
        elif choice == "3":
            print("\n=== CLASS STATISTICAL METRICS (NUMPY) ===")
            print(f"  • Total Students Evaluated : {stats['total_students']}")
            print(f"  • Mean Class Attendance    : {stats['mean_attendance']}%")
            print(f"  • Median Class Attendance  : {stats['median_attendance']}%")
            print(f"  • Standard Deviation       : {stats['std_deviation']}%")
            print(f"  • Minimum Attendance       : {stats['min_attendance']}%")
            print(f"  • Maximum Attendance       : {stats['max_attendance']}%")
            print(f"  • 25th Percentile (Q1)     : {stats['iqr_25']}%")
            print(f"  • 75th Percentile (Q3)     : {stats['iqr_75']}%")
        elif choice == "4":
            print("\n=== ATTENDANCE TRENDS & PATTERNS ===")
            print(f"  • Trend Trajectory         : {trends['trajectory']} (Regression Slope: {trends['slope']})")
            print(f"  • Peak Attendance Date     : {trends['best_day']['DATE']} ({trends['best_day']['Attendance_Pct']}%)")
            print(f"  • Lowest Attendance Date   : {trends['lowest_day']['DATE']} ({trends['lowest_day']['Attendance_Pct']}%)")
            print("\n  Day-of-Week Summary:")
            for day, row in trends['day_summary'].iterrows():
                print(f"    - {day:<10}: {row['Pct']:>6.2f}% ({int(row['Present'])}/{int(row['Total'])})")
        elif choice == "5":
            q = input("Enter Student Name or Roll Number: ")
            search_student(summary, df, q)
        elif choice == "6":
            export_analysis_report(summary, defaulters)
        elif choice in ["7", ""]:
            print("Exiting analysis. Have a great day!")
            break
        else:
            print("Invalid choice, please enter a number from 1 to 7.")


if __name__ == "__main__":
    # If run standalone, locate attendance_records.csv and start
    csv_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "attendance_records.csv")
    run_interactive_menu(csv_file)

# Smart Attendance Management and Analysis System

A comprehensive Python-based attendance tracking and analytics solution designed for academic environments. The system combines real-time daily attendance recording, database persistence, text-to-speech voice announcements, automated WhatsApp notifications, and advanced statistical analysis powered by NumPy and Pandas.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Project Architecture](#project-architecture)
- [Prerequisites](#prerequisites)
- [Installation and Setup](#installation-and-setup)
- [Database Configuration](#database-configuration)
- [Usage Instructions](#usage-instructions)
  - [1. Recording Daily Attendance](#1-recording-daily-attendance)
  - [2. Running Analytics Directly](#2-running-analytics-directly)
  - [3. Interactive Analytics Menu](#3-interactive-analytics-menu)
- [Analytics and Statistical Engine](#analytics-and-statistical-engine)
- [Data Storage Schema](#data-storage-schema)
  - [MySQL Database Schema](#mysql-database-schema)
  - [CSV Datasets](#csv-datasets)
- [Configuration and Customization](#configuration-and-customization)
- [License and Author](#license-and-author)

---

## Overview

The Smart Attendance System manages student attendance workflows from input capture to analytical reporting. When instructors take daily roll call, the system logs records simultaneously into a local MySQL database, a consolidated CSV file, and text logs. Absent students are announced via speech synthesis and notified through WhatsApp messaging. 

Additionally, the analytics engine processes historical attendance to compute attendance percentages, detect defaulters below the mandatory 75% threshold, calculate exact classes required for recovery, evaluate statistical distributions (mean, median, standard deviation, IQR), and identify date-wise and day-of-week attendance patterns using linear regression.

---

## Key Features

- Interactive Roll Call: Console prompt for quick attendance entry (0 for present, 1 for absent).
- Dual Storage Architecture: Synchronous logging to both a relational MySQL database and local CSV datasets.
- Automated Defaulter Detection: Highlights students falling below institutional thresholds (e.g., 75% or 60%).
- Recovery Calculation: Determines the exact consecutive attendance streak needed to return to 75% eligibility.
- Statistical Modeling: NumPy-powered calculation of class averages, median, standard deviation, interquartile ranges (25th and 75th percentiles), and extremes.
- Trend and Pattern Analysis: Linear regression slope modeling over daily attendance to establish class trajectories (improving, declining, or stable) along with day-of-week breakdown.
- Voice Alerts: Text-to-speech audio feedback announcing absent students using pyttsx3.
- WhatsApp Integration: Instant messaging support to notify absent students or guardians using pywhatkit.
- Exportable Reports: Automated generation of structured summary reports in CSV format.

---

## Project Architecture

```text
SL_Project/
|-- attendance.py                  # Core attendance capture, voice output, and WhatsApp module
|-- attendance_analysis.py         # NumPy & Pandas data analytics, statistical engine, and dashboard
|-- attendance_records.csv         # Master log of all recorded attendance sessions
|-- attendance_analysis_report.csv # Generated summary report with student percentages and recovery targets
|-- README.md                      # System documentation
```

---

## Prerequisites

- Python 3.8 or higher
- MySQL Server 8.0 or higher
- Internet connection (required for WhatsApp web messaging)
- Audio output device (for pyttsx3 voice synthesis)

---

## Installation and Setup

1. Clone or download the repository to your local system:
   ```bash
   git clone https://github.com/CodeAadityaGupta/SL_Project.git
   cd SL_Project
   ```

2. Create and activate a Python virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```

3. Install required Python packages:
   ```bash
   pip install numpy pandas mysql-connector-python pyttsx3 pywhatkit
   ```

---

## Database Configuration

The application interfaces with a local MySQL server. Ensure your MySQL service is active and configure the database credentials as outlined below:

1. Log into your MySQL client:
   ```bash
   mysql -u root -p
   ```

2. Create the attendance database:
   ```sql
   CREATE DATABASE IF NOT EXISTS attendance;
   USE attendance;
   ```

3. Create the attendance record table:
   ```sql
   CREATE TABLE IF NOT EXISTS AttenRec (
       ROLLno INT,
       NAME VARCHAR(50),
       ATTENDANCE VARCHAR(15),
       DATE VARCHAR(30)
   );
   ```

4. Database connection parameters are specified in `attendance.py`:
   - Host: `localhost`
   - User: `root`
   - Password: `your_mysql_password` (default in code: `123456`)
   - Database: `attendance`

---

## Usage Instructions

### 1. Recording Daily Attendance

Execute `attendance.py` to launch the standard attendance workflow:
```bash
python attendance.py
```

- The script prompts for each student in the registered roster:
  - Enter `0` for Present
  - Enter `1` for Absent
- Records are saved to MySQL (`AttenRec` table) and `attendance_records.csv`.
- Voice announcements will state absent students.
- WhatsApp notifications will be prepared for numbers configured in `pnumber()`.
- The smart analysis dashboard launches automatically upon completion.

### 2. Running Analytics Directly

To skip interactive marking and run the analytics dashboard directly on existing CSV data, use the `--analyze` or `-a` flag:

```bash
python attendance.py --analyze
```
or run the analysis module directly:
```bash
python attendance_analysis.py
```

### 3. Interactive Analytics Menu

The analytics interface provides an interactive console menu with the following choices:

- `[1] View Student Summary & Percentages`: Tabular overview of total sessions, attended sessions, absent sessions, attendance percentages, and eligibility status.
- `[2] View Low-Attendance (< 75%) Defaulters Alert`: List of defaulters along with consecutive classes required to reach 75%.
- `[3] View Class Statistics & NumPy Metrics`: Mean, median, standard deviation, variance spread, IQR percentiles, and category counts.
- `[4] View Attendance Trends & Trajectory`: Overall trend direction (slope), highest/lowest attended dates, and day-of-week attendance distributions.
- `[5] Search Individual Student Details`: Quick lookup by student name or roll number.
- `[6] Re-export Analysis Report (CSV)`: Writes updated metrics to `attendance_analysis_report.csv`.
- `[7] Exit Analysis`: Exits the interactive console.

---

## Analytics and Statistical Engine

### 1. Eligibility Classification

- Eligible: Attendance >= 75.0%
- Warning: Attendance between 60.0% and 74.99%
- Defaulter / Critical: Attendance < 60.0%

### 2. Defaulter Recovery Formula

For a student with `A` classes attended out of `T` total conducted classes, the minimum consecutive classes `x` needed to achieve target threshold `P` (where `P = 0.75` for 75%) is derived as:

```text
(A + x) / (T + x) >= P
x * (1 - P) >= P * T - A
x = ceil( max(0, (P * T - A) / (1 - P)) )
```

This computation is vectorized using NumPy across all student records.

### 3. Trend Trajectory Calculation

The date-wise attendance percentage series is evaluated using first-degree polynomial fitting (`numpy.polyfit`):
- `slope > +0.15`: Improving Trajectory
- `slope < -0.15`: Declining Trajectory
- `-0.15 <= slope <= +0.15`: Stable Trajectory

---

## Data Storage Schema

### MySQL Database Schema

Table name: `AttenRec`

| Column | Type | Description |
|---|---|---|
| `ROLLno` | INT | Roll number assigned to student |
| `NAME` | VARCHAR(50) | Full name of the student |
| `ATTENDANCE` | VARCHAR(15) | Status string (`present` or `absent`) |
| `DATE` | VARCHAR(30) | Date of session (YYYY-MM-DD) |

### CSV Datasets

1. `attendance_records.csv`:
   - Columns: `ROLLno,NAME,ATTENDANCE,DATE`
   - Purpose: Primary persistent log consumed by the analysis pipeline.

2. `attendance_analysis_report.csv`:
   - Columns: `NAME,Roll_No,Total_Classes,Attended,Absent,Percentage,Status,Classes_Needed_For_75`
   - Purpose: Exported summary report for administrative and parent review.

---

## Configuration and Customization

- Modifying Student Roster:
  Update student definitions and the roster list `i` in `attendance.py`:
  ```python
  a = "Aaditya Gupta        "
  c = "yash Gupta           "
  # Add or edit student names
  i = [a, c, ...]
  ```

- Configuring Mobile Numbers:
  Update the phone number resolver function `pnumber(name)` in `attendance.py`:
  ```python
  def pnumber(name):
      if name == a:
          return "+91XXXXXXXXXX"
  ```

- Adjusting Attendance Thresholds:
  Modify the `threshold` parameter in `detect_low_attendance(summary_df, threshold=75.0)` in `attendance_analysis.py`.

---

## License and Author

- Project Lead & Developer: Aaditya Gupta
- Contact: aaditya31977@gmail.com
- Repository: [CodeAadityaGupta/SL_Project](https://github.com/CodeAadityaGupta/SL_Project)

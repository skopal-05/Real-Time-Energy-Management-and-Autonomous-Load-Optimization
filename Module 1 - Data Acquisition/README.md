# Module 1 - Data Acquisition

## Overview

This module is responsible for generating, validating, and preprocessing industrial energy datasets for the AI-powered Digital Twin system.

The generated datasets simulate different industrial systems and prepare them for downstream AI models such as Energy Forecasting, Scenario Simulation, and Autonomous Load Optimization.

---

## Project Structure

```
Module 1 - Data Acquisition/
│
├── data_collection/
│   ├── production.py
│   ├── compressor.py
│   ├── battery.py
│   ├── boiler.py
│   ├── solar.py
│   ├── grid.py
│   ├── weather.py
│   ├── synthetic_utils.py
│   └── run_all.py
│
├── validation/
│   ├── validate_schema.py
│   ├── validate_missing.py
│   └── validate_ranges.py
│
├── preprocessing/
│   ├── clean_data.py
│   ├── missing_values.py
│   ├── feature_engineering.py
│   └── normalize.py
│
├── outputs/
│   ├── cleaned_data/
│   ├── normalized_data/
│   └── logs/
│
├── requirements.txt
└── README.md
```

---

## Generated Datasets

The module generates synthetic datasets for:

- Air Compressor
- Battery Storage
- Boiler
- Grid
- Production Line A
- Production Line B
- Solar Plant
- Weather

---

## Validation Pipeline

The following validation steps are performed:

- Schema Validation
- Missing Value Validation
- Range Validation

Validation reports are stored in:

```
outputs/logs/
```

---

## Preprocessing Pipeline

The preprocessing pipeline consists of:

### Data Cleaning

- Remove duplicate rows
- Convert timestamp to datetime
- Sort by timestamp
- Standardize column names

### Missing Value Handling

- Linear Interpolation
- Forward Fill
- Backward Fill
- Mode Imputation

### Feature Engineering

Generated features include:

- Hour
- Day
- Month
- Day of Week
- Weekend Indicator
- Cyclic Hour Encoding
- Lag Features
- Rolling Mean
- Rolling Standard Deviation

### Normalization

Numerical features are normalized using Min-Max Scaling.

Normalized datasets are stored in:

```
outputs/normalized_data/
```

---

## Installation

Install the required packages:

```bash
pip install -r requirements.txt
```

---

## Execution Order

### Generate Data

```bash
cd data_collection
py run_all.py
```

### Validation

```bash
cd validation
py validate_schema.py
py validate_missing.py
py validate_ranges.py
```

### Preprocessing

```bash
cd preprocessing
py clean_data.py
py missing_values.py
py feature_engineering.py
py normalize.py
```

---

## Outputs

### Cleaned Data

```
outputs/cleaned_data/
```

### Normalized Data

```
outputs/normalized_data/
```

### Reports

```
outputs/logs/
```

---

## Technologies Used

- Python
- Pandas
- NumPy
- Scikit-Learn

---

## Project

AI-Powered Digital Twin for Real-Time Energy Management and Autonomous Load Optimization in Industrial Manufacturing Systems.
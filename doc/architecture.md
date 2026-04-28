# Architecture Overview

## Current Prototype Architecture

Application data is stored in CSV files and loaded into a Streamlit application.

```text
CSV data sources
      ↓
Data Loader
      ↓
Decision-ready dataset
      ↓
Recommendation Engine
      ↓
Streamlit UI
      ↓
Human Review
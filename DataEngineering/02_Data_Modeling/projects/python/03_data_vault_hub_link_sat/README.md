# Data Vault Architecture (Hub, Link, Satellite)

This project models a basic Data Vault architecture in SQLite. It separates business keys (Hubs), relationships (Links), and descriptive attributes (Satellites) to allow for agile and scalable enterprise data warehousing.

## Overview
- **Hubs:** `hub_customer`, `hub_order` (Store unique business keys)
- **Links:** `link_customer_order` (Store relationships between hubs)
- **Satellites:** `sat_customer_details` (Store context/attributes that change over time)

## How to Run
```bash
python main.py
```

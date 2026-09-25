# Star Schema Generator

This project demonstrates how to generate synthetic transactional data and model it using a Star Schema (Fact and Dimension tables) in an SQLite database.

## Overview
- **Fact Table:** `fact_sales` (contains metrics like quantity and amount, and foreign keys).
- **Dimension Tables:** `dim_product`, `dim_store` (contains descriptive attributes).

## How to Run
```bash
python main.py
```

# Slowly Changing Dimensions (SCD) Type 2 Implementer

This project demonstrates how to implement SCD Type 2 using Python and SQLite. In SCD Type 2, historical data is retained by adding a new row for every change, tracking validity periods with `start_date` and `end_date`, and an `is_current` flag.

## Scenario
A customer (`Bob Jones`) initially lives in `Chicago`, and later moves to `Seattle`. The script correctly closes the old record and creates a new current record.

## How to Run
```bash
python main.py
```

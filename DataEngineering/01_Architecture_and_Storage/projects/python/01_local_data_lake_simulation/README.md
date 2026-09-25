# Local Data Lake Simulation

This project simulates a data lake ingestion process by generating dummy JSON events and organizing them into a partitioned directory structure (e.g., `year=.../month=.../day=...`).

## Usage

Run the script using Python:

```bash
python main.py
```

This will create a `data_lake/raw` directory with the generated partitions and JSON files.

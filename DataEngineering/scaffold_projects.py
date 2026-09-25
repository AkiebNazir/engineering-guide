import os

BASE_DIR = "/Users/njasm/Njasm/AI/engineering-guide/DataEngineering"

TOPICS = [
    "01_Architecture_and_Storage",
    "02_Data_Modeling",
    "03_Data_Ingestion",
    "04_Batch_Processing",
    "05_Stream_Processing",
    "06_Data_Orchestration",
    "07_Data_Transformation",
    "08_Data_Governance_and_Quality"
]

PROJECT_IDEAS = {
    "01_Architecture_and_Storage": ["Local_Data_Lake_Simulation", "Parquet_vs_CSV_Benchmarker", "S3_Bucket_Manager", "Data_Warehouse_Schema_Builder", "Iceberg_Table_Manager"],
    "02_Data_Modeling": ["Star_Schema_Generator", "Snowflake_Schema_Builder", "Data_Vault_Hub_Link_Sat", "SCD_Type_2_Implementer", "Denormalizer_Engine"],
    "03_Data_Ingestion": ["REST_API_Poller", "Web_Scraper_to_DB", "CDC_Log_Tailer", "Webhook_Listener", "FTP_File_Downloader"],
    "04_Batch_Processing": ["Daily_Sales_Aggregator", "Log_Anomaly_Detector", "MapReduce_WordCount", "User_Session_Reconstructor", "Data_Cleansing_Job"],
    "05_Stream_Processing": ["RealTime_Dashboard_Backend", "Fraud_Detection_Engine", "Clickstream_Analyzer", "Sliding_Window_Aggregator", "Kafka_to_DB_Consumer"],
    "06_Data_Orchestration": ["DAG_Dependency_Resolver", "Task_Retry_Handler", "Cron_Job_Scheduler", "Data_Pipeline_Monitor", "Sensor_Wait_Condition"],
    "07_Data_Transformation": ["SQL_Templating_Engine", "JSON_Flattening_Script", "Data_Type_Caster", "Currency_Converter_Pipeline", "PII_Masking_Transformer"],
    "08_Data_Governance_and_Quality": ["Data_Quality_Assertions", "Lineage_Tracker", "Metadata_Catalog_Builder", "Anomaly_Alerting", "Schema_Validation_Gate"]
}

def create_project(topic_path, lang, idx, name):
    prefix = f"{idx:02d}_{name.lower()}"
    proj_dir = os.path.join(topic_path, "projects", lang, prefix)
    os.makedirs(proj_dir, exist_ok=True)
    
    with open(os.path.join(proj_dir, "README.md"), "w") as f:
        f.write(f"# {name.replace('_', ' ')} ({lang.capitalize()})\n\nThis project demonstrates data engineering concepts for this topic.\n\n## Overview\nExpand this section to fully implement the logic.\n")

    if lang == "python":
        with open(os.path.join(proj_dir, "main.py"), "w") as f:
            f.write(f"\"\"\"\nProject: {name}\nLanguage: Python\n\"\"\"\n\ndef main():\n    print('Starting Data Engineering Project...')\n\nif __name__ == '__main__':\n    main()\n")
    else:
        with open(os.path.join(proj_dir, "main.go"), "w") as f:
            f.write(f"// Project: {name}\n// Language: Golang\npackage main\n\nimport \"fmt\"\n\nfunc main() {{\n\tfmt.Println(\"Starting Data Engineering Project...\")\n}}\n")

for topic in TOPICS:
    topic_path = os.path.join(BASE_DIR, topic)
    os.makedirs(topic_path, exist_ok=True)
    ideas = PROJECT_IDEAS.get(topic, [])
    for idx, idea in enumerate(ideas, 1):
        create_project(topic_path, "python", idx, idea)
        create_project(topic_path, "golang", idx, idea)

print("Scaffolded 5 projects per topic successfully.")

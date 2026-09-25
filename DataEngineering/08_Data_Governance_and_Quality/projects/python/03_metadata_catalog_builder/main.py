import json

catalog = {
    "tables": [
        {
            "name": "fct_sales",
            "owner": "data_engineering@company.com",
            "description": "Daily aggregated sales facts.",
            "columns": [
                {"name": "date", "type": "DATE", "description": "Transaction date"},
                {"name": "total_amount", "type": "FLOAT", "description": "Sum of sales"}
            ]
        }
    ]
}

with open('catalog.json', 'w') as f:
    json.dump(catalog, f, indent=4)

print("Generated metadata catalog: catalog.json")

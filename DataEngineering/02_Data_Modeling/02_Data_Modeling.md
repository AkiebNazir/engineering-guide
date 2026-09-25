# Data Modeling

Data modeling is the process of creating a visual representation of either a whole information system or parts of it to communicate connections between data points and structures. In Data Engineering, it defines how data is stored, queried, and updated.

## 1. Dimensional Modeling (Kimball)

Dimensional modeling is designed for data warehouse databases to optimize read performance and intuitive querying for Business Intelligence (BI).

### Fact Tables
- Stores quantitative data (measurements, metrics, or facts) about a business process.
- Examples: Sales amount, discount, quantity ordered.
- Highly granular, contains foreign keys linking to dimension tables.

### Dimension Tables
- Stores descriptive attributes (context) related to the facts.
- Examples: Customer names, locations, product categories, time/dates.
- Usually wider, heavily denormalized, and smaller in row count compared to fact tables.

### Star Schema
The simplest style of dimensional modeling. A central fact table is connected to multiple dimension tables, resembling a star.
- **Pros**: Fast queries, easy to understand.
- **Cons**: Can lead to data redundancy in dimension tables.

```arch
node d_cust "DIM_CUSTOMER" at 0,0 shape=card color=blue sub="customer_id (PK)
name
city"
node d_prod "DIM_PRODUCT" at 1,0 shape=card color=amber sub="product_id (PK)
product_name
category"
node d_date "DIM_DATE" at 2,0 shape=card color=teal sub="date_id (PK)
..."
node f_sales "FACT_SALES" at 1,1 shape=card color=purple sub="order_id
customer_id (FK)
product_id (FK)
date_id (FK)
total_amount"
d_cust -> f_sales
d_prod -> f_sales
d_date -> f_sales
```

### Snowflake Schema
An extension of the Star Schema where dimension tables are normalized into multiple related tables.
- **Pros**: Reduces data redundancy.
- **Cons**: More complex queries requiring more JOINs, potentially slower read performance.

## 2. Slowly Changing Dimensions (SCD)

Dimension data changes over time (e.g., a customer moves to a new city). SCD strategies dictate how to handle these changes.

- **SCD Type 1 (Overwrite)**: Overwrite the old record with the new one. No historical tracking.
- **SCD Type 2 (Add Row)**: Create a new row for the new data. Track history using `start_date`, `end_date`, and an `is_current` flag. (Most common).
- **SCD Type 3 (Add Column)**: Add a new column to store the previous value (e.g., `previous_city`, `current_city`). Limited historical tracking.
- **SCD Type 6 (Hybrid)**: Combines Types 1, 2, and 3.

## 3. Data Vault Modeling

Designed to provide long-term historical storage of data coming from multiple operational systems. Highly scalable and resilient to change.

- **Hubs**: Core business entities (e.g., Customer, Product). Contains a business key.
- **Links**: Relationships between Hubs.
- **Satellites**: Descriptive attributes about Hubs or Links that change over time (similar to SCD Type 2).

```arch
node hc "Hub_Customer" at 0,0 shape=card color=blue
node hp "Hub_Product" at 2,0 shape=card color=amber
node link "Link_Order" at 1,0 shape=card color=purple
node sat "Sat_Customer_Details" at 0,1 icon=db color=teal
hc -> link
hp -> link
hc -> sat
```

## 4. Normalization vs Denormalization

- **Normalization**: Organizing data to minimize redundancy. Breaking large tables into smaller, related ones (OLTP focus).
- **Denormalization**: Combining data into fewer tables to reduce JOINs and improve read performance (OLAP focus).

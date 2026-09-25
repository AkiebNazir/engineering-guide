# Data Modeling: Star Schema & SCDs

When data lands in the Data Warehouse, it cannot remain in its 3rd Normal Form (OLTP) shape. Analysts and BI tools (like Tableau) need data to be easily queryable without writing 15-way JOINs.

## 1. Dimensional Modeling (The Star Schema)

Invented by Ralph Kimball, the Star Schema separates data into two types of tables:

### Fact Tables
- Measurements, metrics, or events. They grow massively over time.
- Examples: `fact_sales`, `fact_pageviews`, `fact_payments`.
- Columns are mostly Foreign Keys and numerical amounts: `date_id`, `product_id`, `store_id`, `revenue_amount`, `discount`.

### Dimension Tables
- Descriptive attributes. They provide the "who, what, where, when".
- Examples: `dim_user`, `dim_product`, `dim_date`, `dim_store`.
- Columns are descriptive strings: `product_name`, `category`, `user_city`.

```arch
%% caption: In a Star Schema, a central Fact table holds the metrics and foreign keys to surrounding Dimension tables which hold the descriptive attributes.
route straight
node user "dim_user" at 0,0 icon=user color=green
node store "dim_store" at 0,2 icon=package color=green
node fact "fact_sales\\n(revenue: $50)" at 2,1 icon=db color=blue
node prod "dim_product" at 4,0 icon=package color=green
node date "dim_date" at 4,2 icon=time color=green

fact -> user
fact -> store
fact -> prod
fact -> date
```

## 2. Slowly Changing Dimensions (SCD)

What happens when a user moves from "New York" to "London"? If we just update `dim_user`, all of their *historical* sales from last year will suddenly look like they happened in London! 

To preserve history for analytical accuracy, we use Slowly Changing Dimensions.

### SCD Type 1 (Overwrite)
Just UPDATE the row. History is lost.
*Use when:* Correcting typos, or when history truly doesn't matter (e.g., updating a user's phone number).

### SCD Type 2 (Add New Row)
When the user moves, do not update the old row. Instead, mark the old row as "expired" and insert a brand new row.
- `user_sk = 101, user_id = 42, city = "New York", is_active = false, valid_to = "2023-12-31"`
- `user_sk = 102, user_id = 42, city = "London", is_active = true, valid_to = "9999-12-31"`

*Use when:* You need perfectly accurate historical reporting. This is the gold standard for Data Warehousing.

### Surrogate Keys (SK)
Notice in SCD Type 2, the `user_id` (42) appears twice. We can no longer use it as the Primary Key in the Data Warehouse.
Instead, Data Engineers generate a **Surrogate Key** (an auto-incrementing integer or UUID) for every row in the Dimension table. 
The Fact table links to the Surrogate Key (`user_sk = 101` for sales before 2024, `user_sk = 102` for sales after).

# Query Lab Datasets (SQL)

Three realistic PostgreSQL datasets for the [SQL Query Lab](../questions.md). Each is one schema,
so they can live side by side in one database. They are generated (deterministically, so answers
never drift) by [`tools/gen_query_lab_data.py`](../../../../../tools/gen_query_lab_data.py): the people,
companies and brands are invented; the cities, countries and coordinates are real.

| Schema | What it models | Tables (rows) |
|---|---|---|
| `shop` | An online store's two years of trading (2024-2025): seasonality with Black Friday and December peaks, growth, cancellations, returns, split payments, reviews | `customers` (2,000), `categories` (32, a 3-level tree), `products` (141, with JSONB `attributes`), `orders` (4,601), `order_items` (8,862), `payments` (4,577), `reviews` (1,844) |
| `hr` | Northwind Labs, a 174-person tech company: a five-level org chart, salary history with raises, projects, attrition and a hiring pipeline with duplicate applications | `departments` (12), `employees` (174), `salary_history` (811), `projects` (24), `employee_projects` (169), `job_applications` (285) |
| `analytics` | Pulseboard, a SaaS app in 2025: signups by channel, daily logins and page views with realistic retention decay, subscriptions with churn and upgrades, and an A/B test | `users` (800), `events` (37,476), `subscriptions` (259), `experiment_assignments` (630) |

The data is deliberately imperfect in the ways real data is, because that's what interview and
production queries are about: customers who never ordered, products never sold, a department with
nobody in it, employees who earn more than their manager, salary ties, duplicate job applications
with different email case, payments that don't add up to the order total, missing phone numbers,
days with no orders.

## Using them

**In the app:** SQL module → **Query Lab**. The datasets load into a real PostgreSQL engine
(PGlite) running in your browser; pick a dataset and query its tables by name. Nothing to
install, works offline and on the hosted site.

**In the lab Postgres** (`docker compose -f docker-compose.databases.yml up -d`, see the
[SQL module](../../README.md)):

```bash
psql "postgresql://dsa:dsa@localhost:5544/dsa" -f content/data-and-apis/SQL/lab/datasets/shop.sql
psql "postgresql://dsa:dsa@localhost:5544/dsa" -f content/data-and-apis/SQL/lab/datasets/hr.sql
psql "postgresql://dsa:dsa@localhost:5544/dsa" -f content/data-and-apis/SQL/lab/datasets/analytics.sql
```

```sql
SET search_path TO shop;      -- then: SELECT * FROM orders LIMIT 5;
```

Each file drops and recreates its own schema, so re-running it resets that dataset. They load in
about a second each and were tested on PostgreSQL 16 (the lab's version) and PostgreSQL 18.

## Schemas

### shop

```text
customers(customer_id PK, first_name, last_name, email UNIQUE, phone NULL, city, region, country,
          signup_at, referred_by -> customers NULL, segment: consumer|business|vip, marketing_opt_in)
categories(category_id PK, name UNIQUE, parent_id -> categories NULL)          -- Electronics > Audio > Headphones
products(product_id PK, sku UNIQUE, name, brand, category_id -> categories (a leaf), price, cost,
         stock, attributes JSONB, launched_at, is_active)
orders(order_id PK, customer_id -> customers, ordered_at, status: placed|shipped|delivered|cancelled|returned,
       ship_city, ship_country, payment_method, coupon_code NULL, shipping_fee, total_amount, delivered_at NULL)
order_items(order_id -> orders, line_no, product_id -> products, quantity, unit_price, discount_pct)  PK(order_id, line_no)
payments(payment_id PK, order_id -> orders, method, amount, status: captured|pending|refunded, paid_at)
reviews(review_id PK, product_id -> products, customer_id -> customers, rating 1-5, title,
        verified_purchase, created_at)  UNIQUE(customer_id, product_id)
```

`total_amount` = sum of `quantity * unit_price * (1 - discount_pct / 100)` plus `shipping_fee`
(free from 50). Timestamps are `timestamptz` in UTC.

### hr

```text
departments(dept_id PK, name UNIQUE, city, country, budget)
employees(emp_id PK, first_name, last_name, email UNIQUE, job_title, level: C-level|VP|Manager|Staff|Senior|Mid|Junior,
          dept_id -> departments, manager_id -> employees NULL, salary, commission_pct NULL (Sales only),
          hire_date, termination_date NULL, birth_date, gender, city, country)
salary_history(emp_id -> employees, salary, effective_from, effective_to NULL (= current), reason)  PK(emp_id, effective_from)
projects(project_id PK, name UNIQUE, dept_id -> departments, start_date, end_date NULL, status, budget)
employee_projects(emp_id -> employees, project_id -> projects, role, hours_per_week)  PK(emp_id, project_id)
job_applications(application_id PK, applicant_name, email, position, applied_at, source, stage)
```

The org chart: CEO → VPs → managers → individual contributors. "Current employees" are those
with `termination_date IS NULL`.

### analytics

```text
users(user_id PK, signup_at, channel: organic|paid_search|social|referral|email, country, device: web|ios|android)
events(event_id PK, user_id -> users, event_type: login|page_view|upgrade_click|payment, event_at, page NULL, amount NULL)
subscriptions(subscription_id PK, user_id -> users, plan: pro|team, started_at, ended_at NULL (= active), mrr)
experiment_assignments(user_id -> users, experiment, variant: A|B, assigned_at, converted)  PK(user_id, experiment)
```

A user's activity is their `login` events: one per active day, followed by page views.

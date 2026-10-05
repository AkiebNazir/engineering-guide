# SQL Query Lab: Interview and Everyday Queries

The queries interviewers ask most often and the ones you write every week at work, against
realistic data. Open them in the app's **Query Lab** (SQL module → Query Lab) to run them in a
real PostgreSQL engine inside your browser, check your answer and reveal the solution; or load
the datasets into the lab Postgres and run them with `psql` (see [the datasets](datasets/README.md)).

Every question names its dataset (`shop`, `hr` or `analytics`), the columns to return and the
sort order, so your result can be checked exactly. Column names don't matter; values and,
where the question says so, row order do. Numbers are compared to 2 decimal places.

<!-- Format, for authors: "## " starts a section, "### " a question, followed by one metadata
     comment, the prompt, "> **Hint:**" lines, then a <details> block holding the solution
     (first ```sql block), the explanation, and optionally a ```sql verify block that checks the
     state after a data-changing solution. webapp/scripts/validate_query_labs.mjs runs them all. -->

## Warm-up: SELECT, WHERE, ORDER BY

### Most expensive products
<!-- id: most-expensive-products | dataset: shop | level: Easy | tags: order by, limit | order: strict -->

List the 10 most expensive **active** products.

Return `name`, `brand`, `price`, most expensive first; break ties by `product_id`.

> **Hint:** Filter with `WHERE is_active`, then `ORDER BY price DESC` and `LIMIT 10`.

<details>
<summary>Solution</summary>

```sql
SELECT name, brand, price
FROM products
WHERE is_active
ORDER BY price DESC, product_id
LIMIT 10;
```

A tie-breaker in `ORDER BY` makes the result deterministic: without it, two products at the same
price can swap places between runs, and so can which one survives `LIMIT`.

</details>

### Opted-in customers in India
<!-- id: opted-in-india | dataset: shop | level: Easy | tags: where, and, order by | order: strict -->

Marketing wants the 15 most recent sign-ups from **India** who opted in to marketing emails.

Return `first_name`, `last_name`, `email`, `city`, `signup_at`, newest first.

> **Hint:** Two conditions joined with `AND`; `marketing_opt_in` is a boolean column.

<details>
<summary>Solution</summary>

```sql
SELECT first_name, last_name, email, city, signup_at
FROM customers
WHERE country = 'India' AND marketing_opt_in
ORDER BY signup_at DESC
LIMIT 15;
```

</details>

### Active but out of stock
<!-- id: active-out-of-stock | dataset: shop | level: Easy | tags: where, boolean | order: any -->

Which products are still listed (`is_active`) but have nothing in stock?

Return `product_id`, `name`, `brand`.

<details>
<summary>Solution</summary>

```sql
SELECT product_id, name, brand
FROM products
WHERE is_active AND stock = 0;
```

</details>

### Who has no manager?
<!-- id: no-manager | dataset: hr | level: Easy | tags: null, is null | order: any -->

Find the employee(s) with no manager.

Return `emp_id`, `first_name`, `last_name`, `job_title`.

> **Hint:** `manager_id = NULL` is never true. Comparisons with NULL yield NULL, not true.

<details>
<summary>Solution</summary>

```sql
SELECT emp_id, first_name, last_name, job_title
FROM employees
WHERE manager_id IS NULL;
```

`NULL` means "unknown", so `x = NULL` is unknown too and `WHERE` drops the row. Always test with
`IS NULL` / `IS NOT NULL` (or `IS DISTINCT FROM` when comparing two nullable columns).

</details>

### Customers without a phone number
<!-- id: missing-phone | dataset: shop | level: Easy | tags: null, count | order: any -->

How many customers have no phone number on file?

Return a single number.

<details>
<summary>Solution</summary>

```sql
SELECT count(*) FROM customers WHERE phone IS NULL;
```

`count(*)` counts rows; `count(phone)` would count only the non-NULL phones, a common trick
question: `count(*) - count(phone)` gives the same answer as this query.

</details>

### Festive coupon orders in December 2025
<!-- id: festive-coupon-orders | dataset: shop | level: Easy | tags: like, dates | order: any -->

How many orders placed in **December 2025** used a coupon code starting with `FESTIVE`?

Return a single number.

> **Hint:** `LIKE 'FESTIVE%'`, and a half-open date range: `>= '2025-12-01' AND < '2026-01-01'`.

<details>
<summary>Solution</summary>

```sql
SELECT count(*)
FROM orders
WHERE coupon_code LIKE 'FESTIVE%'
  AND ordered_at >= '2025-12-01'
  AND ordered_at <  '2026-01-01';
```

The half-open range (`>=` start, `<` next start) is the safe way to filter timestamps: `BETWEEN
'2025-12-01' AND '2025-12-31'` silently drops everything after midnight on the 31st.

</details>

## Aggregation: GROUP BY and HAVING

### Orders and revenue by status
<!-- id: orders-by-status | dataset: shop | level: Easy | tags: group by, sum | order: strict -->

For each order status, how many orders and how much money (`total_amount`)?

Return `status`, `orders`, `revenue`, with the most orders first.

<details>
<summary>Solution</summary>

```sql
SELECT status, count(*) AS orders, sum(total_amount) AS revenue
FROM orders
GROUP BY status
ORDER BY orders DESC;
```

</details>

### Countries with more than 50 customers
<!-- id: countries-over-50 | dataset: shop | level: Easy | tags: group by, having | order: strict -->

Which countries have more than 50 customers?

Return `country`, `customers`, largest first.

> **Hint:** `WHERE` filters rows before grouping; `HAVING` filters groups after.

<details>
<summary>Solution</summary>

```sql
SELECT country, count(*) AS customers
FROM customers
GROUP BY country
HAVING count(*) > 50
ORDER BY customers DESC;
```

</details>

### Average salary by department
<!-- id: avg-salary-by-dept | dataset: hr | level: Easy | tags: group by, avg, join | order: strict -->

Average salary of **current** employees (no `termination_date`) in each department.

Return `department`, `headcount`, `avg_salary` rounded to whole dollars, highest average first.

<details>
<summary>Solution</summary>

```sql
SELECT d.name AS department, count(*) AS headcount, round(avg(e.salary)) AS avg_salary
FROM employees e
JOIN departments d ON d.dept_id = e.dept_id
WHERE e.termination_date IS NULL
GROUP BY d.name
ORDER BY avg_salary DESC;
```

</details>

### Monthly average order value in 2025
<!-- id: monthly-aov-2025 | dataset: shop | level: Medium | tags: date_trunc, avg | order: strict -->

Average order value (AOV) for each month of 2025, counting only orders that were not cancelled.

Return `month` (the first day of the month, as a date), `orders`, `aov` rounded to 2 decimals,
in calendar order.

> **Hint:** `date_trunc('month', ordered_at)::date` turns a timestamp into its month.

<details>
<summary>Solution</summary>

```sql
SELECT date_trunc('month', ordered_at)::date AS month,
       count(*)                              AS orders,
       round(avg(total_amount), 2)           AS aov
FROM orders
WHERE status <> 'cancelled'
  AND ordered_at >= '2025-01-01' AND ordered_at < '2026-01-01'
GROUP BY 1
ORDER BY 1;
```

Look at November and December: order volume roughly doubles while AOV stays close to the
yearly average. Seasonality shows up in counts far more than in basket size.

</details>

### Best-reviewed brands
<!-- id: best-reviewed-brands | dataset: shop | level: Medium | tags: join, having, avg | order: strict -->

Average rating per brand, but only for brands with **at least 50 reviews**.

Return `brand`, `reviews`, `avg_rating` rounded to 2 decimals, best rating first.

<details>
<summary>Solution</summary>

```sql
SELECT p.brand, count(*) AS reviews, round(avg(r.rating), 2) AS avg_rating
FROM reviews r
JOIN products p ON p.product_id = r.product_id
GROUP BY p.brand
HAVING count(*) >= 50
ORDER BY avg_rating DESC, p.brand;
```

The `HAVING` threshold matters: a brand with two 5-star reviews would otherwise top the list.
Ranking by an average without a minimum sample size is a classic analytics mistake.

</details>

### Payment method share
<!-- id: payment-method-share | dataset: shop | level: Medium | tags: window, percentage | order: strict -->

What share of all orders used each payment method?

Return `payment_method`, `orders`, `pct` (percentage of all orders, rounded to 1 decimal),
largest share first.

> **Hint:** `sum(count(*)) OVER ()` is the grand total, computed after grouping.

<details>
<summary>Solution</summary>

```sql
SELECT payment_method,
       count(*) AS orders,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct
FROM orders
GROUP BY payment_method
ORDER BY orders DESC;
```

A window function over an aggregate runs after `GROUP BY`, so `sum(count(*)) OVER ()` adds up
the per-method counts. Note `100.0`: integer division (`100 * 3 / 7`) would truncate.

</details>

## Joins

### Top customers by lifetime spend
<!-- id: top-customers-spend | dataset: shop | level: Easy | tags: join, group by, top n | order: strict -->

The 10 customers who have spent the most on **delivered** orders.

Return `customer_id`, `customer` (first and last name with a space), `orders`, `spent`, biggest
spender first.

<details>
<summary>Solution</summary>

```sql
SELECT c.customer_id,
       c.first_name || ' ' || c.last_name AS customer,
       count(*)            AS orders,
       sum(o.total_amount) AS spent
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
WHERE o.status = 'delivered'
GROUP BY c.customer_id
ORDER BY spent DESC
LIMIT 10;
```

Grouping by the primary key (`c.customer_id`) lets you select the customer's other columns:
Postgres knows they are functionally dependent on it.

</details>

### Customers who never ordered
<!-- id: never-ordered | dataset: shop | level: Easy | tags: left join, not exists, anti join | order: strict -->

List customers who have never placed an order.

Return `customer_id`, `email`, `signup_at`, by `customer_id`.

> **Hint:** An anti-join: `LEFT JOIN ... WHERE o.order_id IS NULL`, or `NOT EXISTS (...)`.

<details>
<summary>Solution</summary>

```sql
SELECT c.customer_id, c.email, c.signup_at
FROM customers c
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id)
ORDER BY c.customer_id;
```

`NOT EXISTS` and `LEFT JOIN ... IS NULL` give the same answer and usually the same plan.
Avoid `NOT IN (SELECT customer_id FROM orders)`: if that subquery ever returns a NULL, `NOT IN`
returns no rows at all.

</details>

### Products never sold
<!-- id: products-never-sold | dataset: shop | level: Easy | tags: left join, anti join | order: any -->

Which products have never appeared in any order?

Return `product_id`, `name`, `launched_at`.

<details>
<summary>Solution</summary>

```sql
SELECT p.product_id, p.name, p.launched_at
FROM products p
LEFT JOIN order_items i ON i.product_id = p.product_id
WHERE i.product_id IS NULL;
```

</details>

### Employees who earn more than their manager
<!-- id: earn-more-than-manager | dataset: hr | level: Medium | tags: self join, classic | order: any -->

The classic self-join: find employees whose salary is higher than their direct manager's.

Return `employee` (first and last name), `salary`, `manager` (first and last name), `manager_salary`.

> **Hint:** Join `employees` to itself: `employees e JOIN employees m ON m.emp_id = e.manager_id`.

<details>
<summary>Solution</summary>

```sql
SELECT e.first_name || ' ' || e.last_name AS employee, e.salary,
       m.first_name || ' ' || m.last_name AS manager,  m.salary AS manager_salary
FROM employees e
JOIN employees m ON m.emp_id = e.manager_id
WHERE e.salary > m.salary;
```

Aliases are what make a self-join readable: `e` is the employee row, `m` the manager row of the
same table.

</details>

### Departments with no employees
<!-- id: empty-departments | dataset: hr | level: Easy | tags: left join | order: any -->

Which departments have nobody in them?

Return `dept_id`, `name`, `city`.

<details>
<summary>Solution</summary>

```sql
SELECT d.dept_id, d.name, d.city
FROM departments d
LEFT JOIN employees e ON e.dept_id = d.dept_id
WHERE e.emp_id IS NULL;
```

</details>

### Skip-level managers
<!-- id: skip-level-manager | dataset: hr | level: Medium | tags: self join, left join | order: strict -->

For every employee in the **Design** department, show their manager and their manager's manager
(the "skip-level"). Either may be missing.

Return `employee`, `manager`, `skip_level` (each as first and last name, NULL when there is none),
ordered by `emp_id`.

<details>
<summary>Solution</summary>

```sql
SELECT e.first_name || ' ' || e.last_name   AS employee,
       m.first_name || ' ' || m.last_name   AS manager,
       mm.first_name || ' ' || mm.last_name AS skip_level
FROM employees e
JOIN departments d    ON d.dept_id = e.dept_id
LEFT JOIN employees m  ON m.emp_id  = e.manager_id
LEFT JOIN employees mm ON mm.emp_id = m.manager_id
WHERE d.name = 'Design'
ORDER BY e.emp_id;
```

`LEFT JOIN`s keep the top of the chain: the VP has a manager (the CEO) but no skip-level,
and an inner join would silently drop them.

</details>

### Revenue by top-level category
<!-- id: revenue-by-top-category | dataset: shop | level: Medium | tags: join, multi-table | order: strict -->

Products sit in leaf categories (Phones, Laptops, ...) whose parent chain ends at a top-level
category (Electronics, Fashion, ...). Using `categories.parent_id`, compute revenue
(`quantity * unit_price * (1 - discount_pct / 100.0)`) from **delivered** orders per **top-level**
category. Categories are at most three levels deep.

Return `category`, `revenue` rounded to 2 decimals, highest first.

> **Hint:** Join `categories` up to three times (`c1`, `c2`, `c3`) and take
> `coalesce(c3.name, c2.name, c1.name)`, or solve it with a recursive CTE.

<details>
<summary>Solution</summary>

```sql
SELECT coalesce(c3.name, c2.name, c1.name) AS category,
       round(sum(i.quantity * i.unit_price * (1 - i.discount_pct / 100.0)), 2) AS revenue
FROM order_items i
JOIN orders o     ON o.order_id = i.order_id AND o.status = 'delivered'
JOIN products p   ON p.product_id = i.product_id
JOIN categories c1 ON c1.category_id = p.category_id
LEFT JOIN categories c2 ON c2.category_id = c1.parent_id
LEFT JOIN categories c3 ON c3.category_id = c2.parent_id
GROUP BY 1
ORDER BY revenue DESC;
```

Fixed-depth self-joins work when the depth is known and small. When it isn't, the recursive
version (see "Category breadcrumbs" below) handles any depth.

</details>

### Customers who referred more than one person
<!-- id: top-referrers | dataset: shop | level: Medium | tags: self join, having | order: strict -->

`customers.referred_by` points to the customer who referred them. Who referred two or more
customers?

Return `customer_id`, `customer` (first and last name), `referrals`, most referrals first, then
by `customer_id`.

<details>
<summary>Solution</summary>

```sql
SELECT r.customer_id, r.first_name || ' ' || r.last_name AS customer, count(*) AS referrals
FROM customers c
JOIN customers r ON r.customer_id = c.referred_by
GROUP BY r.customer_id
HAVING count(*) >= 2
ORDER BY referrals DESC, r.customer_id;
```

</details>

## Subqueries and CTEs

### Second highest salary
<!-- id: second-highest-salary | dataset: hr | level: Medium | tags: subquery, distinct, classic | order: any -->

The most-asked SQL interview question: what is the **second highest distinct** salary in the
company? If there were none, the answer should be NULL rather than no row.

Return a single value.

> **Hint:** Several ways: `max(salary)` below the overall max; `DISTINCT ... OFFSET 1`; `DENSE_RANK() = 2`.
> **Hint:** Wrapping a query in a scalar subquery `SELECT (...)` turns "no rows" into NULL.

<details>
<summary>Solution</summary>

```sql
SELECT (
    SELECT DISTINCT salary
    FROM employees
    ORDER BY salary DESC
    OFFSET 1 LIMIT 1
) AS second_highest_salary;
```

Follow-ups interviewers ask: "now the N-th highest" (`OFFSET n-1`, or `DENSE_RANK() = n`),
"per department" (see "Top three earners per department"), and "what if two people tie for
first?" (`DISTINCT` handles that: the second *distinct* salary).

</details>

### Earning above the department average
<!-- id: above-dept-average | dataset: hr | level: Medium | tags: correlated subquery, window | order: strict -->

Find current employees who earn more than the average salary of their own department (averaged
over current employees).

Return `emp_id`, `name` (first and last), `department`, `salary`, `dept_avg` rounded to whole
dollars, ordered by department name, then salary descending.

> **Hint:** A correlated subquery computes the average for the outer row's department; a window
> function `avg(salary) OVER (PARTITION BY dept_id)` does the same in one pass.

<details>
<summary>Solution</summary>

```sql
WITH current_staff AS (
    SELECT e.*, avg(e.salary) OVER (PARTITION BY e.dept_id) AS dept_avg
    FROM employees e
    WHERE e.termination_date IS NULL
)
SELECT s.emp_id, s.first_name || ' ' || s.last_name AS name, d.name AS department,
       s.salary, round(s.dept_avg) AS dept_avg
FROM current_staff s
JOIN departments d ON d.dept_id = s.dept_id
WHERE s.salary > s.dept_avg
ORDER BY d.name, s.salary DESC;
```

The window version reads each row once; the correlated subquery version
(`WHERE salary > (SELECT avg(salary) FROM employees x WHERE x.dept_id = e.dept_id ...)`) is
easier to say out loud and Postgres plans it well enough at this size.

</details>

### Orders above the average order value
<!-- id: above-average-orders | dataset: shop | level: Easy | tags: scalar subquery | order: any -->

How many delivered orders have a total above the average total of all delivered orders?

Return a single number.

<details>
<summary>Solution</summary>

```sql
SELECT count(*)
FROM orders
WHERE status = 'delivered'
  AND total_amount > (SELECT avg(total_amount) FROM orders WHERE status = 'delivered');
```

</details>

### Bought a phone and headphones
<!-- id: phone-and-headphones | dataset: shop | level: Medium | tags: exists, intersect | order: strict -->

Which customers have bought at least one product in the **Phones** category *and* at least one in
**Headphones** (in any orders, any status except cancelled)?

Return `customer_id`, ordered by `customer_id`.

> **Hint:** `INTERSECT` two sets of customer ids, or use two `EXISTS` conditions.

<details>
<summary>Solution</summary>

```sql
WITH bought AS (
    SELECT DISTINCT o.customer_id, c.name AS category
    FROM orders o
    JOIN order_items i ON i.order_id = o.order_id
    JOIN products p    ON p.product_id = i.product_id
    JOIN categories c  ON c.category_id = p.category_id
    WHERE o.status <> 'cancelled'
)
SELECT customer_id FROM bought WHERE category = 'Phones'
INTERSECT
SELECT customer_id FROM bought WHERE category = 'Headphones'
ORDER BY customer_id;
```

The same shape answers "bought X but not Y" with `EXCEPT`. A third way is grouping:
`GROUP BY customer_id HAVING count(DISTINCT category) = 2` over the two categories.

</details>

### Priced above their category average
<!-- id: above-category-average | dataset: shop | level: Medium | tags: correlated subquery | order: strict -->

Which products cost more than the average price of the products in their own (leaf) category?

Return `product_id`, `name`, `price`, `category_avg` rounded to 2 decimals, ordered by
`product_id`.

<details>
<summary>Solution</summary>

```sql
SELECT p.product_id, p.name, p.price, round(c.avg_price, 2) AS category_avg
FROM products p
JOIN (SELECT category_id, avg(price) AS avg_price FROM products GROUP BY category_id) c
  ON c.category_id = p.category_id
WHERE p.price > c.avg_price
ORDER BY p.product_id;
```

</details>

## Window functions

### Top three earners per department
<!-- id: top3-per-department | dataset: hr | level: Hard | tags: dense_rank, top n per group, classic | order: strict -->

LeetCode 185 with real data: for each department, list everyone whose salary is among the top
three **distinct** salaries of that department (ties included). Current employees only.

Return `department`, `employee` (first and last name), `salary`, ordered by department, then
salary descending, then employee name.

> **Hint:** `DENSE_RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC)`, then keep rank <= 3.
> **Hint:** You can't filter on a window function in `WHERE` of the same query; use a CTE or subquery.

<details>
<summary>Solution</summary>

```sql
WITH ranked AS (
    SELECT d.name AS department,
           e.first_name || ' ' || e.last_name AS employee,
           e.salary,
           dense_rank() OVER (PARTITION BY e.dept_id ORDER BY e.salary DESC) AS rnk
    FROM employees e
    JOIN departments d ON d.dept_id = e.dept_id
    WHERE e.termination_date IS NULL
)
SELECT department, employee, salary
FROM ranked
WHERE rnk <= 3
ORDER BY department, salary DESC, employee;
```

Why `DENSE_RANK`: with salaries 200, 200, 180, 150 `RANK` gives 1, 1, 3, 4 (one salary short of
three), `ROW_NUMBER` gives 1, 2, 3, 4 (drops a tie arbitrarily), and `DENSE_RANK` gives
1, 1, 2, 3, which is exactly "top three distinct salaries".

</details>

### ROW_NUMBER vs RANK vs DENSE_RANK
<!-- id: rank-functions-compared | dataset: hr | level: Medium | tags: row_number, rank, dense_rank | order: strict -->

Show the difference between the three ranking functions on the **Engineering** department:
rank current employees by salary (highest first).

Return `employee` (first and last name), `salary`, `row_number`, `rank`, `dense_rank`, ordered by
salary descending, then `emp_id`. Use `emp_id` as the tie-breaker inside `ROW_NUMBER` too.

<details>
<summary>Solution</summary>

```sql
SELECT e.first_name || ' ' || e.last_name AS employee, e.salary,
       row_number() OVER (ORDER BY e.salary DESC, e.emp_id) AS row_number,
       rank()       OVER (ORDER BY e.salary DESC)           AS rank,
       dense_rank() OVER (ORDER BY e.salary DESC)           AS dense_rank
FROM employees e
JOIN departments d ON d.dept_id = e.dept_id
WHERE d.name = 'Engineering' AND e.termination_date IS NULL
ORDER BY e.salary DESC, e.emp_id;
```

Find a tie in the output: `row_number` keeps counting, `rank` repeats then skips, `dense_rank`
repeats without skipping.

</details>

### Running revenue total for 2025
<!-- id: running-total-2025 | dataset: shop | level: Medium | tags: sum over, running total | order: strict -->

Monthly revenue of delivered orders in 2025 and the running total for the year.

Return `month` (first day, as a date), `revenue`, `running_total`, in calendar order.

<details>
<summary>Solution</summary>

```sql
WITH monthly AS (
    SELECT date_trunc('month', ordered_at)::date AS month, sum(total_amount) AS revenue
    FROM orders
    WHERE status = 'delivered' AND ordered_at >= '2025-01-01' AND ordered_at < '2026-01-01'
    GROUP BY 1
)
SELECT month, revenue, sum(revenue) OVER (ORDER BY month) AS running_total
FROM monthly
ORDER BY month;
```

With `ORDER BY` inside `OVER`, the default frame is "from the start up to this row", which is a
running total. Aggregating in a CTE first keeps the window simple; the one-query form
`sum(sum(total_amount)) OVER (ORDER BY date_trunc('month', ordered_at))` also works, but only if
`GROUP BY` uses that exact expression rather than the ordinal `1`.

</details>

### Month-over-month growth
<!-- id: mom-growth | dataset: shop | level: Medium | tags: lag, growth | order: strict -->

Month-over-month revenue growth for delivered orders across both years.

Return `month` (first day, as a date), `revenue`, `prev_revenue`, `growth_pct` (rounded to 1
decimal; NULL for the first month), in calendar order.

> **Hint:** `lag(revenue) OVER (ORDER BY month)` is the previous row's value.

<details>
<summary>Solution</summary>

```sql
WITH monthly AS (
    SELECT date_trunc('month', ordered_at)::date AS month, sum(total_amount) AS revenue
    FROM orders
    WHERE status = 'delivered'
    GROUP BY 1
)
SELECT month, revenue,
       lag(revenue) OVER (ORDER BY month) AS prev_revenue,
       round(100.0 * (revenue - lag(revenue) OVER (ORDER BY month))
                   / lag(revenue) OVER (ORDER BY month), 1) AS growth_pct
FROM monthly
ORDER BY month;
```

`lag` returns NULL on the first row, and NULL propagates through the arithmetic, so the first
month's growth is NULL rather than a misleading 0 or an error.

</details>

### Seven-day moving average
<!-- id: moving-average-7d | dataset: shop | level: Hard | tags: frame, rows between, moving average | order: strict -->

Daily revenue (non-cancelled orders) in **December 2025** with a trailing 7-day moving average.
Every day has orders in this month.

Return `day` (as a date), `revenue`, `avg_7d` (average of this day and the 6 before it, rounded to
2 decimals), in date order. For the first days of the month, average over the days available.

<details>
<summary>Solution</summary>

```sql
WITH daily AS (
    SELECT ordered_at::date AS day, sum(total_amount) AS revenue
    FROM orders
    WHERE status <> 'cancelled' AND ordered_at >= '2025-12-01' AND ordered_at < '2026-01-01'
    GROUP BY 1
)
SELECT day, revenue,
       round(avg(revenue) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS avg_7d
FROM daily
ORDER BY day;
```

`ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` counts rows, not days: if a day had no orders it
would be missing and the window would stretch over 8+ calendar days. In real data you'd first
fill gaps from `generate_series` (see "Days without orders").

</details>

### Time to second order
<!-- id: days-to-second-order | dataset: shop | level: Hard | tags: row_number, lead, retention | order: any -->

For customers with at least two orders, how many days passed between their first and second
order? (All statuses count.)

Return `customer_id`, `first_order` (date), `second_order` (date), `days_between` (integer).

> **Hint:** Number each customer's orders with `ROW_NUMBER()`; `lead(ordered_at)` gives the next one.

<details>
<summary>Solution</summary>

```sql
WITH seq AS (
    SELECT customer_id, ordered_at,
           row_number() OVER (PARTITION BY customer_id ORDER BY ordered_at, order_id) AS n,
           lead(ordered_at) OVER (PARTITION BY customer_id ORDER BY ordered_at, order_id) AS next_at
    FROM orders
)
SELECT customer_id, ordered_at::date AS first_order, next_at::date AS second_order,
       next_at::date - ordered_at::date AS days_between
FROM seq
WHERE n = 1 AND next_at IS NOT NULL;
```

Subtracting two `date`s gives an integer number of days; subtracting two `timestamptz`s gives an
`interval`.

</details>

### Best seller in each category
<!-- id: best-seller-per-category | dataset: shop | level: Hard | tags: row_number, top 1 per group | order: strict -->

The best-selling product (by units sold in non-cancelled orders) in each **leaf** category. If two
products tie, take the one with the lower `product_id`.

Return `category`, `product`, `units`, ordered by `category`.

<details>
<summary>Solution</summary>

```sql
WITH units AS (
    SELECT p.category_id, p.product_id, p.name, sum(i.quantity) AS units
    FROM order_items i
    JOIN orders o   ON o.order_id = i.order_id AND o.status <> 'cancelled'
    JOIN products p ON p.product_id = i.product_id
    GROUP BY p.category_id, p.product_id, p.name
), ranked AS (
    SELECT u.*, row_number() OVER (PARTITION BY category_id ORDER BY units DESC, product_id) AS rn
    FROM units u
)
SELECT c.name AS category, r.name AS product, r.units
FROM ranked r
JOIN categories c ON c.category_id = r.category_id
WHERE r.rn = 1
ORDER BY c.name;
```

"Top 1 per group" is `ROW_NUMBER() = 1`; Postgres also offers `DISTINCT ON (category_id) ...
ORDER BY category_id, units DESC, product_id`, shorter but Postgres-only.

</details>

### Median salary by department
<!-- id: median-salary | dataset: hr | level: Medium | tags: percentile_cont, median | order: strict -->

Median and average salary of current employees in each department that has staff.

Return `department`, `median_salary`, `avg_salary` (both rounded to whole dollars), ordered by
department.

<details>
<summary>Solution</summary>

```sql
SELECT d.name AS department,
       round(percentile_cont(0.5) WITHIN GROUP (ORDER BY e.salary)::numeric) AS median_salary,
       round(avg(e.salary)) AS avg_salary
FROM employees e
JOIN departments d ON d.dept_id = e.dept_id
WHERE e.termination_date IS NULL
GROUP BY d.name
ORDER BY d.name;
```

`percentile_cont` interpolates between the two middle values for an even count;
`percentile_disc` returns an actual value from the set. Comparing median to mean shows skew:
a few very high salaries pull the mean above the median.

</details>

### The 80/20 rule
<!-- id: pareto-customers | dataset: shop | level: Hard | tags: cumulative sum, pareto | order: any -->

What percentage of paying customers generate 80% of delivered-order revenue? Rank customers by
spend, accumulate their share, and count how many it takes to reach 80%.

Return `customers_for_80pct`, `paying_customers`, `pct_of_customers` (rounded to 1 decimal).

> **Hint:** `sum(spent) OVER (ORDER BY spent DESC)` divided by the total is each customer's
> cumulative share; count the rows until it reaches 0.8.

<details>
<summary>Solution</summary>

```sql
WITH spend AS (
    SELECT customer_id, sum(total_amount) AS spent
    FROM orders WHERE status = 'delivered'
    GROUP BY customer_id
), cum AS (
    SELECT spent,
           sum(spent) OVER (ORDER BY spent DESC, customer_id) / sum(spent) OVER () AS cum_share
    FROM spend
)
SELECT count(*) FILTER (WHERE cum_share <= 0.8) + 1 AS customers_for_80pct,
       count(*)                                   AS paying_customers,
       round(100.0 * (count(*) FILTER (WHERE cum_share <= 0.8) + 1) / count(*), 1) AS pct_of_customers
FROM cum;
```

The `+ 1` counts the customer whose purchase crosses the 80% line. Heavy-tailed spend (a few
whales) is normal in retail, and it is why "top customers" lists matter.

</details>

## Dates and times

### Busiest day of the week
<!-- id: busiest-weekday | dataset: shop | level: Easy | tags: extract, to_char | order: strict -->

How many orders are placed on each day of the week?

Return `weekday` (full name, like `Monday`), `orders`, ordered Monday to Sunday.

> **Hint:** `extract(isodow FROM ordered_at)` gives 1 for Monday through 7 for Sunday;
> `trim(to_char(ordered_at, 'Day'))` gives the name.

<details>
<summary>Solution</summary>

```sql
SELECT trim(to_char(ordered_at, 'Day')) AS weekday, count(*) AS orders
FROM orders
GROUP BY extract(isodow FROM ordered_at), 1
ORDER BY extract(isodow FROM ordered_at);
```

`to_char(..., 'Day')` pads names to 9 characters, hence `trim`. The timestamps are UTC; a real
report would convert to the store's time zone first: `ordered_at AT TIME ZONE 'Asia/Kolkata'`.

</details>

### Delivery time by country
<!-- id: delivery-time-by-country | dataset: shop | level: Medium | tags: interval, epoch | order: strict -->

Average delivery time in days (from `ordered_at` to `delivered_at`) for delivered orders, per
shipping country, for countries with at least 100 delivered orders.

Return `ship_country`, `orders`, `avg_days` rounded to 1 decimal, slowest first.

<details>
<summary>Solution</summary>

```sql
SELECT ship_country, count(*) AS orders,
       round(avg(extract(epoch FROM delivered_at - ordered_at) / 86400)::numeric, 1) AS avg_days
FROM orders
WHERE status = 'delivered'
GROUP BY ship_country
HAVING count(*) >= 100
ORDER BY avg_days DESC, ship_country;
```

`delivered_at - ordered_at` is an `interval`; `extract(epoch FROM ...)` turns it into seconds, so
dividing by 86400 gives fractional days.

</details>

### Years of service
<!-- id: years-of-service | dataset: hr | level: Medium | tags: age, date_part | order: strict -->

The 10 longest-serving current employees, with their completed years of service as of
**2025-12-31**.

Return `employee` (first and last name), `hire_date`, `years`, longest service first, then by
`emp_id`.

<details>
<summary>Solution</summary>

```sql
SELECT first_name || ' ' || last_name AS employee, hire_date,
       extract(year FROM age(DATE '2025-12-31', hire_date))::int AS years
FROM employees
WHERE termination_date IS NULL
ORDER BY hire_date, emp_id
LIMIT 10;
```

`age()` returns a calendar-aware interval ("9 years 3 mons 12 days"), so `extract(year ...)`
gives completed years, not 365-day blocks.

</details>

### Daily active users
<!-- id: daily-active-users | dataset: analytics | level: Easy | tags: count distinct, dau | order: strict -->

Daily active users (distinct users with a `login` event) for **1 to 7 September 2025**.

Return `day` (as a date), `dau`, in date order.

<details>
<summary>Solution</summary>

```sql
SELECT event_at::date AS day, count(DISTINCT user_id) AS dau
FROM events
WHERE event_type = 'login'
  AND event_at >= '2025-09-01' AND event_at < '2025-09-08'
GROUP BY 1
ORDER BY 1;
```

</details>

### Monthly active users
<!-- id: monthly-active-users | dataset: analytics | level: Easy | tags: date_trunc, count distinct, mau | order: strict -->

Monthly active users (distinct users with any event) for every month of 2025.

Return `month` (first day, as a date), `mau`, in calendar order.

<details>
<summary>Solution</summary>

```sql
SELECT date_trunc('month', event_at)::date AS month, count(DISTINCT user_id) AS mau
FROM events
GROUP BY 1
ORDER BY 1;
```

Note that `count(DISTINCT ...)` cannot be summed across months: a user active in January and
February counts once in each month but once overall.

</details>

### Days without orders
<!-- id: days-without-orders | dataset: shop | level: Hard | tags: generate_series, gaps | order: strict -->

Were there any days in **2024** with no orders at all? Generate the calendar and find the gaps.

Return `day` (as a date), in date order.

> **Hint:** `generate_series(DATE '2024-01-01', DATE '2024-12-31', INTERVAL '1 day')` builds the
> calendar; anti-join it with the order dates.

<details>
<summary>Solution</summary>

```sql
SELECT d::date AS day
FROM generate_series(DATE '2024-01-01', DATE '2024-12-31', INTERVAL '1 day') AS d
WHERE NOT EXISTS (
    SELECT 1 FROM orders o
    WHERE o.ordered_at >= d AND o.ordered_at < d + INTERVAL '1 day'
)
ORDER BY 1;
```

Missing days are invisible to `GROUP BY`: you can only find what isn't there by comparing
against a complete calendar.

</details>

## Strings, CASE and JSON

### Email providers
<!-- id: email-providers | dataset: shop | level: Easy | tags: split_part, string | order: strict -->

Count customers by email provider (the part after `@`).

Return `domain`, `customers`, largest first, then by domain.

<details>
<summary>Solution</summary>

```sql
SELECT split_part(email, '@', 2) AS domain, count(*) AS customers
FROM customers
GROUP BY 1
ORDER BY customers DESC, domain;
```

</details>

### Order size bands
<!-- id: order-size-bands | dataset: shop | level: Easy | tags: case | order: strict -->

Classify non-cancelled orders by total: `small` under 50, `medium` from 50 up to (not including)
200, `large` from 200. How many in each band, and how much revenue?

Return `band`, `orders`, `revenue`, ordered small, medium, large.

<details>
<summary>Solution</summary>

```sql
SELECT CASE WHEN total_amount < 50  THEN 'small'
            WHEN total_amount < 200 THEN 'medium'
            ELSE 'large' END AS band,
       count(*) AS orders,
       sum(total_amount) AS revenue
FROM orders
WHERE status <> 'cancelled'
GROUP BY 1
ORDER BY min(total_amount);
```

`CASE` stops at the first true branch, so the second condition only needs `< 200`.
`ORDER BY min(total_amount)` sorts the bands by size without a lookup table.

</details>

### Headcount pivot
<!-- id: headcount-pivot | dataset: hr | level: Medium | tags: pivot, filter, case | order: strict -->

Pivot current headcount: one row per department, one column per level.

Return `department`, `junior`, `mid`, `senior`, `staff`, `managers` (level `Manager`), `total`,
ordered by department. Only departments with at least one current employee.

> **Hint:** `count(*) FILTER (WHERE level = 'Junior')` is a conditional count; `sum(CASE ...)`
> does the same in every SQL dialect.

<details>
<summary>Solution</summary>

```sql
SELECT d.name AS department,
       count(*) FILTER (WHERE e.level = 'Junior')  AS junior,
       count(*) FILTER (WHERE e.level = 'Mid')     AS mid,
       count(*) FILTER (WHERE e.level = 'Senior')  AS senior,
       count(*) FILTER (WHERE e.level = 'Staff')   AS staff,
       count(*) FILTER (WHERE e.level = 'Manager') AS managers,
       count(*) AS total
FROM employees e
JOIN departments d ON d.dept_id = e.dept_id
WHERE e.termination_date IS NULL
GROUP BY d.name
ORDER BY d.name;
```

</details>

### Phones with lots of storage
<!-- id: phones-storage-jsonb | dataset: shop | level: Medium | tags: jsonb, ->> | order: strict -->

`products.attributes` is JSONB. Find phones (category `Phones`) with at least 256 GB of storage.

Return `name`, `price`, `storage_gb` (as an integer), `color`, ordered by price.

> **Hint:** `attributes->>'storage_gb'` returns text; cast it with `::int` before comparing.

<details>
<summary>Solution</summary>

```sql
SELECT p.name, p.price, (p.attributes->>'storage_gb')::int AS storage_gb, p.attributes->>'color' AS color
FROM products p
JOIN categories c ON c.category_id = p.category_id
WHERE c.name = 'Phones' AND (p.attributes->>'storage_gb')::int >= 256
ORDER BY p.price;
```

`->` returns JSONB, `->>` returns text. Comparing the text `'64'` with `'256'` would be a string
comparison, and `'64' > '256'`.

</details>

### Available in size M
<!-- id: size-m-jsonb-array | dataset: shop | level: Medium | tags: jsonb, containment, @> | order: any -->

Fashion products store their sizes as a JSON array, e.g. `{"sizes": ["S", "M", "L"]}`. Which
products come in size `M`?

Return `product_id`, `name`, `sizes` (the JSON array).

> **Hint:** The containment operator: `attributes @> '{"sizes": ["M"]}'`. A GIN index can serve it.

<details>
<summary>Solution</summary>

```sql
SELECT product_id, name, attributes->'sizes' AS sizes
FROM products
WHERE attributes @> '{"sizes": ["M"]}';
```

`@>` asks "does the left document contain the right one?", and for arrays that means "contains
these elements". With `CREATE INDEX ON products USING gin (attributes)` it stays fast on
millions of rows.

</details>

## Data quality and cleanup

### Duplicate job applications
<!-- id: duplicate-applications | dataset: hr | level: Medium | tags: duplicates, group by, having, lower | order: strict -->

Some candidates applied twice for the same position, sometimes with their email in different
case. Find every (email, position) pair that appears more than once, ignoring email case.

Return `email` (lower-case), `position`, `applications`, ordered by email then position.

<details>
<summary>Solution</summary>

```sql
SELECT lower(email) AS email, position, count(*) AS applications
FROM job_applications
GROUP BY lower(email), position
HAVING count(*) > 1
ORDER BY 1, 2;
```

Normalising before grouping (`lower`, `trim`) is the whole trick of real-world deduplication.
Grouping on raw `email` would miss the case-only duplicates.

</details>

### Delete the duplicates
<!-- id: delete-duplicate-applications | dataset: hr | level: Hard | tags: delete, row_number, duplicates | order: any -->

Now delete the duplicates, keeping only the **earliest** application (lowest `applied_at`, then
lowest `application_id`) for each (lower-case email, position) pair.

Write the `DELETE`. The checker then counts what's left in `job_applications`.

> **Hint:** Number the rows of each group with `ROW_NUMBER() OVER (PARTITION BY lower(email),
> position ORDER BY applied_at, application_id)` and delete everything with a number above 1.

<details>
<summary>Solution</summary>

```sql
DELETE FROM job_applications
WHERE application_id IN (
    SELECT application_id
    FROM (
        SELECT application_id,
               row_number() OVER (PARTITION BY lower(email), position
                                  ORDER BY applied_at, application_id) AS rn
        FROM job_applications
    ) ranked
    WHERE rn > 1
);
```

In production, run the inner `SELECT` first to see exactly which rows will go, and do it in a
transaction: `BEGIN; DELETE ...; SELECT ...; COMMIT;` (or `ROLLBACK`). The lab runs every attempt
inside a transaction and rolls it back, so you can try as often as you like.

```sql verify
SELECT count(*) AS remaining,
       count(DISTINCT (lower(email), position)) AS distinct_pairs
FROM job_applications;
```

</details>

### Payments that don't add up
<!-- id: payment-reconciliation | dataset: shop | level: Medium | tags: reconciliation, having | order: strict -->

Finance reconciles payments against orders. Find orders where the sum of payments differs from
`total_amount` (ignore orders without any payment).

Return `order_id`, `total_amount`, `paid`, `difference` (`total_amount - paid`), ordered by
`order_id`.

<details>
<summary>Solution</summary>

```sql
SELECT o.order_id, o.total_amount, p.paid, o.total_amount - p.paid AS difference
FROM orders o
JOIN (SELECT order_id, sum(amount) AS paid FROM payments GROUP BY order_id) p
  ON p.order_id = o.order_id
WHERE p.paid <> o.total_amount
ORDER BY o.order_id;
```

Aggregate the many-side (payments) **before** joining. Joining first and then summing would
multiply amounts by the number of matching rows on any other joined table, the "fan-out"
bug that inflates totals.

</details>

## Analytics classics

### Repeat purchase rate
<!-- id: repeat-purchase-rate | dataset: shop | level: Medium | tags: having, rate | order: any -->

Of the customers who placed at least one non-cancelled order, what percentage placed two or more?

Return `customers`, `repeat_customers`, `repeat_rate_pct` (rounded to 1 decimal).

<details>
<summary>Solution</summary>

```sql
WITH per_customer AS (
    SELECT customer_id, count(*) AS orders
    FROM orders
    WHERE status <> 'cancelled'
    GROUP BY customer_id
)
SELECT count(*) AS customers,
       count(*) FILTER (WHERE orders >= 2) AS repeat_customers,
       round(100.0 * count(*) FILTER (WHERE orders >= 2) / count(*), 1) AS repeat_rate_pct
FROM per_customer;
```

</details>

### Year-over-year growth by month
<!-- id: yoy-growth | dataset: shop | level: Hard | tags: self join, lag, yoy | order: strict -->

Compare each month of 2025 with the same month of 2024 (delivered-order revenue).

Return `month_num` (1-12), `revenue_2024`, `revenue_2025`, `yoy_pct` (rounded to 1 decimal),
ordered by month.

<details>
<summary>Solution</summary>

```sql
SELECT extract(month FROM ordered_at)::int AS month_num,
       sum(total_amount) FILTER (WHERE extract(year FROM ordered_at) = 2024) AS revenue_2024,
       sum(total_amount) FILTER (WHERE extract(year FROM ordered_at) = 2025) AS revenue_2025,
       round(100.0 * (sum(total_amount) FILTER (WHERE extract(year FROM ordered_at) = 2025)
                    - sum(total_amount) FILTER (WHERE extract(year FROM ordered_at) = 2024))
                   / sum(total_amount) FILTER (WHERE extract(year FROM ordered_at) = 2024), 1) AS yoy_pct
FROM orders
WHERE status = 'delivered'
GROUP BY 1
ORDER BY 1;
```

Year-over-year removes seasonality: December always beats July, so the useful question is
whether this December beat last December.

</details>

### Frequently bought together
<!-- id: bought-together | dataset: shop | level: Hard | tags: self join, market basket | order: strict -->

Market-basket analysis: which pairs of products appear in the same order most often?

Return the top 10 pairs as `product_a`, `product_b` (product names, with `product_a` having the
lower `product_id`), `orders_together`, most frequent first, then by the two product ids.

> **Hint:** Self-join `order_items` on `order_id` with `a.product_id < b.product_id`, so each pair
> is counted once.

<details>
<summary>Solution</summary>

```sql
SELECT pa.name AS product_a, pb.name AS product_b, count(*) AS orders_together
FROM order_items a
JOIN order_items b ON b.order_id = a.order_id AND a.product_id < b.product_id
JOIN products pa ON pa.product_id = a.product_id
JOIN products pb ON pb.product_id = b.product_id
GROUP BY a.product_id, b.product_id, pa.name, pb.name
ORDER BY orders_together DESC, a.product_id, b.product_id
LIMIT 10;
```

`<` instead of `<>` keeps (A, B) and drops (B, A), and also drops (A, A).

</details>

### Day-1 retention by signup month
<!-- id: d1-retention-cohort | dataset: analytics | level: Hard | tags: cohort, retention | order: strict -->

For each signup month, what share of users logged in again the **day after** they signed up?

Return `cohort` (signup month, first day, as a date), `users`, `retained_d1`, `d1_pct` (rounded to
1 decimal), in calendar order.

> **Hint:** Compare dates, not timestamps: `e.event_at::date = u.signup_at::date + 1`.

<details>
<summary>Solution</summary>

```sql
SELECT date_trunc('month', u.signup_at)::date AS cohort,
       count(*) AS users,
       count(*) FILTER (WHERE EXISTS (
           SELECT 1 FROM events e
           WHERE e.user_id = u.user_id AND e.event_type = 'login'
             AND e.event_at::date = u.signup_at::date + 1)) AS retained_d1,
       round(100.0 * count(*) FILTER (WHERE EXISTS (
           SELECT 1 FROM events e
           WHERE e.user_id = u.user_id AND e.event_type = 'login'
             AND e.event_at::date = u.signup_at::date + 1)) / count(*), 1) AS d1_pct
FROM users u
GROUP BY 1
ORDER BY 1;
```

`EXISTS` inside `FILTER` counts each user at most once no matter how many logins they had that
day. A join plus `count(*)` would count logins, not users.

</details>

### Longest login streak
<!-- id: longest-streak | dataset: analytics | level: Hard | tags: gaps and islands, row_number | order: strict -->

The famous "gaps and islands" problem: find the 5 users with the longest run of consecutive days
with a login.

Return `user_id`, `streak_days`, `streak_start` (date), `streak_end` (date), longest first, then
by `user_id`.

> **Hint:** For consecutive dates, `day - row_number()` is constant: group by it.
> **Hint:** Deduplicate first: a user can log in several times a day.

<details>
<summary>Solution</summary>

```sql
WITH days AS (
    SELECT DISTINCT user_id, event_at::date AS day
    FROM events WHERE event_type = 'login'
), islands AS (
    SELECT user_id, day,
           day - (row_number() OVER (PARTITION BY user_id ORDER BY day))::int AS island
    FROM days
)
SELECT user_id, count(*) AS streak_days, min(day) AS streak_start, max(day) AS streak_end
FROM islands
GROUP BY user_id, island
ORDER BY streak_days DESC, user_id
LIMIT 5;
```

Each consecutive day adds 1 to both `day` and `row_number`, so their difference stays the same
for the whole streak and changes after any gap. The same trick finds sessions, outages and
"three days in a row" questions.

</details>

### Three consecutive days
<!-- id: three-consecutive-days | dataset: analytics | level: Medium | tags: lag, lead, consecutive | order: any -->

How many users ever logged in on **at least three consecutive days**?

Return a single number.

<details>
<summary>Solution</summary>

```sql
WITH days AS (
    SELECT DISTINCT user_id, event_at::date AS day
    FROM events WHERE event_type = 'login'
), marked AS (
    SELECT user_id, day,
           lead(day, 2) OVER (PARTITION BY user_id ORDER BY day) AS day_plus_2
    FROM days
)
SELECT count(DISTINCT user_id)
FROM marked
WHERE day_plus_2 = day + 2;
```

After deduplication, if the row two ahead is exactly two days later, the three days in between
are consecutive. The gaps-and-islands version (`HAVING count(*) >= 3`) gives the same answer.

</details>

### A/B test results
<!-- id: ab-test-results | dataset: analytics | level: Medium | tags: ab test, conversion | order: strict -->

The pricing page experiment `pricing_page_v2` assigned users to variants A (control) and B. What
was each variant's conversion rate?

Return `variant`, `users`, `conversions`, `conversion_pct` (rounded to 2 decimals), ordered by
variant.

<details>
<summary>Solution</summary>

```sql
SELECT variant, count(*) AS users,
       count(*) FILTER (WHERE converted) AS conversions,
       round(100.0 * count(*) FILTER (WHERE converted) / count(*), 2) AS conversion_pct
FROM experiment_assignments
WHERE experiment = 'pricing_page_v2'
GROUP BY variant
ORDER BY variant;
```

The obvious follow-up is "is the difference real?". With a few hundred users per arm, a gap of
a few points can easily be noise; you'd run a two-proportion z-test before declaring a winner.

</details>

### Current MRR by plan
<!-- id: mrr-by-plan | dataset: analytics | level: Easy | tags: saas, mrr | order: strict -->

Monthly recurring revenue (MRR) from subscriptions that are still active (no `ended_at`).

Return `plan`, `subscribers`, `mrr`, highest MRR first.

<details>
<summary>Solution</summary>

```sql
SELECT plan, count(*) AS subscribers, sum(mrr) AS mrr
FROM subscriptions
WHERE ended_at IS NULL
GROUP BY plan
ORDER BY mrr DESC;
```

</details>

### Monthly churn
<!-- id: monthly-churn | dataset: analytics | level: Hard | tags: churn, saas, generate_series | order: strict -->

For each month from February to December 2025: how many subscriptions were active at the start of
the month, how many ended during it, and the churn rate.

Return `month` (first day, as a date), `active_at_start`, `churned`, `churn_pct` (rounded to 1
decimal; NULL when nothing was active), in calendar order.

> **Hint:** Generate the months with `generate_series`; a subscription is active at the start of
> month `m` if `started_at < m` and (`ended_at` is NULL or `ended_at >= m`).

<details>
<summary>Solution</summary>

```sql
SELECT m::date AS month,
       count(*) FILTER (WHERE s.started_at < m AND (s.ended_at IS NULL OR s.ended_at >= m)) AS active_at_start,
       count(*) FILTER (WHERE s.started_at < m AND s.ended_at >= m AND s.ended_at < m + INTERVAL '1 month') AS churned,
       round(100.0 * count(*) FILTER (WHERE s.started_at < m AND s.ended_at >= m AND s.ended_at < m + INTERVAL '1 month')
                   / nullif(count(*) FILTER (WHERE s.started_at < m AND (s.ended_at IS NULL OR s.ended_at >= m)), 0), 1) AS churn_pct
FROM generate_series(DATE '2025-02-01', DATE '2025-12-01', INTERVAL '1 month') AS m
CROSS JOIN subscriptions s
GROUP BY m
ORDER BY m;
```

`nullif(x, 0)` turns a zero denominator into NULL, so the division returns NULL instead of
failing with "division by zero". Note that an upgrade (pro to team) ends one subscription and
starts another: a real churn report would exclude those.

</details>

## Recursive queries and history

### Reporting chain to the CEO
<!-- id: reporting-chain | dataset: hr | level: Hard | tags: recursive cte, hierarchy | order: strict -->

Show the full management chain above employee **1005**, from their direct manager up to the CEO.

Return `level` (1 = direct manager), `emp_id`, `name` (first and last), `job_title`, ordered by
level.

> **Hint:** A recursive CTE: start from employee 1005's manager, then repeatedly join to the
> previous row's manager.

<details>
<summary>Solution</summary>

```sql
WITH RECURSIVE chain AS (
    SELECT m.emp_id, m.first_name, m.last_name, m.job_title, m.manager_id, 1 AS level
    FROM employees e
    JOIN employees m ON m.emp_id = e.manager_id
    WHERE e.emp_id = 1005
  UNION ALL
    SELECT m.emp_id, m.first_name, m.last_name, m.job_title, m.manager_id, c.level + 1
    FROM chain c
    JOIN employees m ON m.emp_id = c.manager_id
)
SELECT level, emp_id, first_name || ' ' || last_name AS name, job_title
FROM chain
ORDER BY level;
```

The anchor (before `UNION ALL`) runs once; the recursive part runs again for each new row until
it produces nothing, which happens at the CEO, whose `manager_id` is NULL.

</details>

### Total headcount under each VP
<!-- id: headcount-under-vp | dataset: hr | level: Hard | tags: recursive cte, tree | order: strict -->

For each VP, how many current employees report to them **directly or indirectly**?

Return `vp` (first and last name), `department`, `reports`, largest org first, then by VP name.

<details>
<summary>Solution</summary>

```sql
WITH RECURSIVE org AS (
    SELECT emp_id AS vp_id, emp_id
    FROM employees
    WHERE level = 'VP'
  UNION ALL
    SELECT o.vp_id, e.emp_id
    FROM org o
    JOIN employees e ON e.manager_id = o.emp_id
)
SELECT v.first_name || ' ' || v.last_name AS vp, d.name AS department, count(*) AS reports
FROM org o
JOIN employees v   ON v.emp_id = o.vp_id
JOIN employees e   ON e.emp_id = o.emp_id
JOIN departments d ON d.dept_id = v.dept_id
WHERE o.emp_id <> o.vp_id AND e.termination_date IS NULL
GROUP BY v.emp_id, d.name
ORDER BY reports DESC, vp;
```

Carrying the root (`vp_id`) through the recursion is the standard way to aggregate a whole
subtree per root.

</details>

### Category breadcrumbs
<!-- id: category-breadcrumbs | dataset: shop | level: Medium | tags: recursive cte, string_agg, path | order: strict -->

Build a breadcrumb for every category, like `Electronics > Audio > Headphones`.

Return `category_id`, `breadcrumb`, ordered by `breadcrumb`.

<details>
<summary>Solution</summary>

```sql
WITH RECURSIVE tree AS (
    SELECT category_id, name::text AS breadcrumb
    FROM categories
    WHERE parent_id IS NULL
  UNION ALL
    SELECT c.category_id, t.breadcrumb || ' > ' || c.name
    FROM categories c
    JOIN tree t ON c.parent_id = t.category_id
)
SELECT category_id, breadcrumb
FROM tree
ORDER BY breadcrumb;
```

Going top-down, each level appends its own name to the parent's path. The `::text` cast in the
anchor matters: the recursive part's column type must match the anchor's.

</details>

### Salary on a past date
<!-- id: salary-as-of | dataset: hr | level: Hard | tags: temporal, effective dates | order: strict -->

`salary_history` stores each salary with the date range it applied to (`effective_to` is NULL for
the current one). What was the total annual payroll of the **Data Science** department on
**2023-01-01** (only people employed then)?

Return `employees`, `payroll`.

> **Hint:** A row applies on date D when `effective_from <= D` and (`effective_to` is NULL or
> `effective_to >= D`).

<details>
<summary>Solution</summary>

```sql
SELECT count(*) AS employees, sum(h.salary) AS payroll
FROM salary_history h
JOIN employees e   ON e.emp_id = h.emp_id
JOIN departments d ON d.dept_id = e.dept_id
WHERE d.name = 'Data Science'
  AND h.effective_from <= DATE '2023-01-01'
  AND (h.effective_to IS NULL OR h.effective_to >= DATE '2023-01-01')
  AND (e.termination_date IS NULL OR e.termination_date >= DATE '2023-01-01');
```

This "effective dating" pattern (a type-2 slowly changing dimension) keeps full history: any past
state is one range predicate away, which is how payroll, pricing and insurance systems work.

</details>

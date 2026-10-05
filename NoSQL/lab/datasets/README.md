# Query Lab Datasets (MongoDB and Redis)

The data behind the [MongoDB](../mongodb-questions.md) and [Redis](../redis-questions.md) Query
Labs. It is the **same store** as the SQL lab's `shop` schema (same ids, customers, orders and
products), modelled the way each database is used, so you can compare the three approaches on
identical data. Generated deterministically by
[`tools/gen_query_lab_data.py`](../../../tools/gen_query_lab_data.py).

## MongoDB: `mongodb/*.json`

| Collection | Documents | Shape |
|---|---|---|
| `customers` | 2,000 | `{ _id, name: { first, last }, email, phone?, address: { city, region, country, location: GeoJSON Point }, segment, signed_up, marketing_opt_in, referred_by? }` |
| `products` | 141 | `{ _id, sku, name, brand, category: ["Electronics", "Audio", "Headphones"], price, stock, attributes: {...varies by category}, active, launched_at, rating: { avg, count }, tags: [...] }` |
| `orders` | 4,601 | `{ _id, customer: { _id, name, city, country }, ordered_at, status, items: [{ product_id, name, category, qty, price, discount_pct? }], shipping: { city, country, fee }, payment: { method, status }, coupon?, total, status_history: [{ status, at }] }` |
| `reviews` | 1,844 | `{ _id, product_id, customer_id, rating, title, verified, created_at }` |

Design choices worth noticing (the labs ask about them): an order **embeds** its line items and a
**snapshot** of the customer (both change together with the order and are read with it), while
reviews **reference** products and customers (unbounded, read separately). Optional fields are
absent rather than `null`. Dates are real dates (EJSON `{"$date": ...}` in the files).

Load them into the lab MongoDB (`docker compose -f docker-compose.databases.yml up -d`):

```bash
for c in customers products orders reviews; do
  mongoimport --uri "mongodb://localhost:27018/shop?directConnection=true" \
    --collection "$c" --jsonArray --drop --file "NoSQL/lab/datasets/mongodb/$c.json"
done
mongosh "mongodb://localhost:27018/shop?directConnection=true"
```

## Redis: `redis/seed.redis`

About 1,300 commands that build 343 keys, one family per real-world use:

| Keys | Type | Use |
|---|---|---|
| `product:<id>` | hash | product cache (cache-aside); `product:101` and `:102` expire in an hour |
| `customer:<id>` | hash | profile cache |
| `bestsellers` | sorted set | product ranking by units sold |
| `leaderboard:2025-W40`, `leaderboard:2025-W41` | sorted set | weekly game leaderboards |
| `pageviews:<page>` | string | counters |
| `ratelimit:user:<id>:<minute>` | string + TTL | fixed-window rate limits |
| `session:<token>` | string + TTL | login sessions |
| `recent:customer:<id>` | list | recently viewed (capped at 5) |
| `cart:customer:<id>` | hash | shopping carts (field = product, value = quantity) |
| `following:<id>` | set | social graph |
| `tags:product:<id>`, `products:tag:<tag>` | set | tagging, both directions |
| `dau:<date>` | bitmap | daily active users (bit = user id), 2025-09-01 to 09-07 |
| `uniques:<date>` | HyperLogLog | unique visitors per day |
| `stores` | geo | 36 store locations (real city coordinates) |
| `stream:orders` | stream | the last 40 orders as events |
| `config:features`, `config:maintenance_mode` | hash, string | feature flags |

Load it into the lab Redis (`redis-cli` has no comment syntax, so strip the `#` lines):

```bash
grep -v '^#' NoSQL/lab/datasets/redis/seed.redis | redis-cli -p 6390
```

In the app, the Redis lab runs the same file in an in-browser Redis that implements the commands
used here. It was checked against Redis 7 command by command. Two documented differences:
`PFCOUNT` is exact in the browser (real HyperLogLog is ~0.81% approximate), and set members are
returned sorted (real Redis returns them in no particular order).

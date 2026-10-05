# MongoDB Query Lab: Interview and Everyday Queries

The MongoDB queries you write every day and the ones interviewers ask about, against the `shop`
dataset as documents: the same customers, products, orders and reviews as the SQL lab, modelled
the MongoDB way (an order embeds its line items, its customer snapshot and its status history).

Open them in the app's **Query Lab** (NoSQL module → Query Lab) to run them in the browser with
`mongosh` syntax, check your answer and reveal the solution, or import the collections into the
lab MongoDB and run them in `mongosh` (see [the datasets](datasets/README.md)).

Each question states the exact shape to return. Documents are compared by content: field order
doesn't matter, field names and values do, and numbers are compared to 2 decimal places. Where
the question asks for a sort, the order matters too.

<!-- Format, for authors: same as SQL/lab/questions.md. Solutions are mongosh code (```js); the
     value of the last expression is the answer. A ```js verify block runs after a write. -->

## Finding documents

### Customers in Japan
<!-- id: customers-in-japan | dataset: shop | level: Easy | tags: find, dot notation, projection | order: strict -->

Find customers whose address is in **Japan**.

Return documents `{ _id, email }` sorted by `_id`.

> **Hint:** Query a nested field with dot notation in quotes: `{ "address.country": "Japan" }`.

<details>
<summary>Solution</summary>

```js
db.customers.find({ "address.country": "Japan" }, { email: 1 }).sort({ _id: 1 })
```

A projection that includes fields (`{ email: 1 }`) returns `_id` too unless you exclude it with
`_id: 0`.

</details>

### Electronics between 100 and 200
<!-- id: electronics-price-range | dataset: shop | level: Easy | tags: find, range, array | order: strict -->

Find products in the **Electronics** category priced from 100 to 200 inclusive.
`category` is an array path like `["Electronics", "Audio", "Headphones"]`.

Return `{ name, price }` (no `_id`), cheapest first, then by name.

> **Hint:** A plain equality on an array field matches if *any* element is equal:
> `{ category: "Electronics" }`.

<details>
<summary>Solution</summary>

```js
db.products.find(
  { category: "Electronics", price: { $gte: 100, $lte: 200 } },
  { _id: 0, name: 1, price: 1 }
).sort({ price: 1, name: 1 })
```

Matching an array with a scalar is MongoDB's most convenient surprise: no `$in`, no unwinding.
To match the whole array exactly you'd write `{ category: ["Electronics", "Phones"] }`.

</details>

### Cancelled or returned orders
<!-- id: cancelled-or-returned | dataset: shop | level: Easy | tags: $in, countDocuments | order: any -->

How many orders were cancelled or returned?

Return the number.

<details>
<summary>Solution</summary>

```js
db.orders.countDocuments({ status: { $in: ["cancelled", "returned"] } })
```

`countDocuments` runs a real query; `estimatedDocumentCount()` reads collection metadata (fast,
but no filter).

</details>

### Orders that include a laptop
<!-- id: orders-with-laptop | dataset: shop | level: Easy | tags: array of documents, dot notation | order: any -->

How many orders contain at least one item from the **Laptops** category?

Return the number.

<details>
<summary>Solution</summary>

```js
db.orders.countDocuments({ "items.category": "Laptops" })
```

Dot notation reaches into arrays of sub-documents: `items.category` matches if any item's
category matches.

</details>

### One line with big quantity and price
<!-- id: elemmatch-line | dataset: shop | level: Medium | tags: $elemMatch, arrays, classic | order: any -->

How many orders have a **single line item** with a quantity of at least 3 **and** a price above 100?
(The two conditions must hold for the same item.)

Return the number.

> **Hint:** `{ "items.qty": { $gte: 3 }, "items.price": { $gt: 100 } }` can match two different items.

<details>
<summary>Solution</summary>

```js
db.orders.countDocuments({ items: { $elemMatch: { qty: { $gte: 3 }, price: { $gt: 100 } } } })
```

The classic interview trap: with dot notation each condition may be satisfied by a different
element (one item with qty 3 at $20, another with qty 1 at $900). `$elemMatch` requires one
element to satisfy all conditions.

</details>

### Customers without a phone
<!-- id: no-phone | dataset: shop | level: Easy | tags: $exists | order: any -->

How many customers have no `phone` field?

Return the number.

<details>
<summary>Solution</summary>

```js
db.customers.countDocuments({ phone: { $exists: false } })
```

`{ phone: null }` would also match documents where the field exists with value `null`; `$exists`
asks only about presence.

</details>

### "Pro" products
<!-- id: pro-products-regex | dataset: shop | level: Easy | tags: regex | order: strict -->

Find products whose name contains the word **Pro** (as a whole word, so "Protein" doesn't count).

Return `{ name }` (no `_id`), sorted by name.

<details>
<summary>Solution</summary>

```js
db.products.find({ name: /\bPro\b/ }, { _id: 0, name: 1 }).sort({ name: 1 })
```

`\b` is a word boundary. A regex that isn't anchored with `^` can't use an index efficiently: for
search across text, a text index or Atlas Search is the tool.

</details>

### Orders with five items
<!-- id: five-item-orders | dataset: shop | level: Easy | tags: $size | order: any -->

How many orders have exactly five line items?

Return the number.

<details>
<summary>Solution</summary>

```js
db.orders.countDocuments({ items: { $size: 5 } })
```

`$size` only takes an exact number. For "more than 3" use `$expr` with the aggregation
`$size` operator (next section), or store an item count you can index.

</details>

### Black Friday 2025
<!-- id: black-friday-orders | dataset: shop | level: Easy | tags: dates, range | order: any -->

How many orders were placed on Black Friday, **28 November 2025** (UTC)?

Return the number.

<details>
<summary>Solution</summary>

```js
db.orders.countDocuments({
  ordered_at: { $gte: ISODate("2025-11-28"), $lt: ISODate("2025-11-29") }
})
```

Dates are real BSON dates, so compare them with dates, never with strings.

</details>

### Countries we ship to
<!-- id: ship-countries | dataset: shop | level: Easy | tags: distinct | order: any -->

Which countries have orders been shipped to?

Return the list of distinct `shipping.country` values.

<details>
<summary>Solution</summary>

```js
db.orders.distinct("shipping.country")
```

</details>

### Page 3 of the catalogue
<!-- id: pagination | dataset: shop | level: Easy | tags: sort, skip, limit, pagination | order: strict -->

The catalogue lists products by price (highest first, ties by `_id`), 10 per page. Return
**page 3**.

Return `{ _id, name, price }`.

<details>
<summary>Solution</summary>

```js
db.products.find({}, { name: 1, price: 1 }).sort({ price: -1, _id: 1 }).skip(20).limit(10)
```

`skip` still walks past every skipped document, so deep pages get slow. For infinite scroll,
paginate by range instead: remember the last `(price, _id)` and query below it.

</details>

## Aggregation pipeline

### Orders by status
<!-- id: orders-by-status | dataset: shop | level: Easy | tags: $group, $sort | order: strict -->

Count orders by status.

Return `{ _id: <status>, orders }`, most orders first.

<details>
<summary>Solution</summary>

```js
db.orders.aggregate([
  { $group: { _id: "$status", orders: { $sum: 1 } } },
  { $sort: { orders: -1 } }
])
```

</details>

### Monthly revenue in 2025
<!-- id: monthly-revenue-2025 | dataset: shop | level: Medium | tags: $match, $group, $dateToString | order: strict -->

Revenue (`total`) of delivered orders for each month of 2025.

Return `{ _id: "YYYY-MM", orders, revenue }` with revenue rounded to 2 decimals, in calendar order.

<details>
<summary>Solution</summary>

```js
db.orders.aggregate([
  { $match: { status: "delivered",
              ordered_at: { $gte: ISODate("2025-01-01"), $lt: ISODate("2026-01-01") } } },
  { $group: { _id: { $dateToString: { format: "%Y-%m", date: "$ordered_at" } },
              orders: { $sum: 1 },
              revenue: { $sum: "$total" } } },
  { $set: { revenue: { $round: ["$revenue", 2] } } },
  { $sort: { _id: 1 } }
])
```

Put `$match` first: it can use an index and it shrinks everything that follows.

</details>

### Top five products by units sold
<!-- id: top-products-units | dataset: shop | level: Medium | tags: $unwind, $group, top n | order: strict -->

Which five products sold the most units across non-cancelled orders?

Return `{ _id: <product_id>, name, units }`, most units first, ties by `_id`.

> **Hint:** `$unwind: "$items"` turns one order with 3 items into 3 documents.

<details>
<summary>Solution</summary>

```js
db.orders.aggregate([
  { $match: { status: { $ne: "cancelled" } } },
  { $unwind: "$items" },
  { $group: { _id: "$items.product_id", name: { $first: "$items.name" }, units: { $sum: "$items.qty" } } },
  { $sort: { units: -1, _id: 1 } },
  { $limit: 5 }
])
```

Embedding the product name in each line item (denormalising) is what lets this run without a
`$lookup`.

</details>

### Best-rated products
<!-- id: best-rated-lookup | dataset: shop | level: Medium | tags: $lookup, $group, having | order: strict -->

From the `reviews` collection, find the five products with the highest average rating among
products with **at least 20 reviews**, and bring in each product's name from `products`.

Return `{ _id: <product_id>, name, reviews, avg_rating }` with `avg_rating` rounded to 2 decimals,
best first, ties by `_id`.

<details>
<summary>Solution</summary>

```js
db.reviews.aggregate([
  { $group: { _id: "$product_id", reviews: { $sum: 1 }, avg_rating: { $avg: "$rating" } } },
  { $match: { reviews: { $gte: 20 } } },
  { $sort: { avg_rating: -1, _id: 1 } },
  { $limit: 5 },
  { $lookup: { from: "products", localField: "_id", foreignField: "_id", as: "product" } },
  { $project: { name: { $first: "$product.name" }, reviews: 1, avg_rating: { $round: ["$avg_rating", 2] } } }
])
```

A `$match` after `$group` is MongoDB's `HAVING`. Doing the `$lookup` after `$limit` joins 5
documents instead of every product.

</details>

### Top customers by spend
<!-- id: top-customers | dataset: shop | level: Medium | tags: $group, embedded snapshot | order: strict -->

The five customers with the highest spend on delivered orders.

Return `{ _id: <customer _id>, name, orders, spent }` with `spent` rounded to 2 decimals, biggest
spender first.

<details>
<summary>Solution</summary>

```js
db.orders.aggregate([
  { $match: { status: "delivered" } },
  { $group: { _id: "$customer._id", name: { $first: "$customer.name" },
              orders: { $sum: 1 }, spent: { $sum: "$total" } } },
  { $set: { spent: { $round: ["$spent", 2] } } },
  { $sort: { spent: -1 } },
  { $limit: 5 }
])
```

The order stores a snapshot of the customer (`customer.name`, `city`): it shows who the order
was for at the time, even if the customer later changes their name.

</details>

### Order size buckets
<!-- id: order-buckets | dataset: shop | level: Medium | tags: $bucket | order: strict -->

Group all orders into total-amount buckets: `[0, 50)`, `[50, 200)`, `[200, 1000)` and everything
from 1000 up as `"1000+"`.

Return `{ _id: <lower bound or "1000+">, orders }` in bucket order.

<details>
<summary>Solution</summary>

```js
db.orders.aggregate([
  { $bucket: { groupBy: "$total", boundaries: [0, 50, 200, 1000],
               default: "1000+", output: { orders: { $sum: 1 } } } }
])
```

`$bucketAuto` picks the boundaries for you, aiming for evenly sized buckets.

</details>

### Two reports in one query
<!-- id: facet-report | dataset: shop | level: Medium | tags: $facet | order: any -->

In a single aggregation, return both the number of orders per status and per payment method.

Return one document `{ by_status: [{ _id, n }...], by_method: [{ _id, n }...] }`, each list sorted by
`_id`.

<details>
<summary>Solution</summary>

```js
db.orders.aggregate([
  { $facet: {
      by_status: [{ $group: { _id: "$status", n: { $sum: 1 } } }, { $sort: { _id: 1 } }],
      by_method: [{ $group: { _id: "$payment.method", n: { $sum: 1 } } }, { $sort: { _id: 1 } }]
  } }
])
```

`$facet` runs several sub-pipelines over the same input: the typical use is a search page that
needs results and the counts for each filter in one round trip.

</details>

### Orders with more than three items
<!-- id: expr-size | dataset: shop | level: Medium | tags: $expr, $size | order: any -->

How many orders have **more than three** line items?

Return `{ orders: <n> }`.

<details>
<summary>Solution</summary>

```js
db.orders.aggregate([
  { $match: { $expr: { $gt: [{ $size: "$items" }, 3] } } },
  { $count: "orders" }
])
```

`$expr` lets a query use aggregation expressions, here computing the array size on the fly.
It can't use a normal index for that comparison.

</details>

### Only the discounted items
<!-- id: filter-discounted-items | dataset: shop | level: Medium | tags: $filter, arrays | order: strict -->

For orders placed on **24 December 2025**, keep only the line items that had a discount
(`discount_pct` present), and drop orders left with none.

Return `{ _id, discounted: [...items] }` sorted by `_id`.

<details>
<summary>Solution</summary>

```js
db.orders.aggregate([
  { $match: { ordered_at: { $gte: ISODate("2025-12-24"), $lt: ISODate("2025-12-25") } } },
  { $project: { discounted: { $filter: { input: "$items", cond: { $gt: ["$$this.discount_pct", 0] } } } } },
  { $match: { "discounted.0": { $exists: true } } },
  { $sort: { _id: 1 } }
])
```

`$filter` keeps array elements matching a condition (`$$this` is the current element) without
unwinding. `"discounted.0": { $exists: true }` is the idiom for "array is not empty".

</details>

### Revenue by customer segment
<!-- id: revenue-by-segment | dataset: shop | level: Hard | tags: $lookup, join | order: strict -->

The order's customer snapshot doesn't include the segment, so join `orders` to `customers`.
Revenue of delivered orders per customer segment.

Return `{ _id: <segment>, orders, revenue }` with revenue rounded to 2 decimals, highest revenue
first.

<details>
<summary>Solution</summary>

```js
db.orders.aggregate([
  { $match: { status: "delivered" } },
  { $lookup: { from: "customers", localField: "customer._id", foreignField: "_id", as: "c" } },
  { $group: { _id: { $first: "$c.segment" }, orders: { $sum: 1 }, revenue: { $sum: "$total" } } },
  { $set: { revenue: { $round: ["$revenue", 2] } } },
  { $sort: { revenue: -1 } }
])
```

`$lookup` always produces an array, even for a one-to-one match: hence `$first`. If you join
like this on every request, that's a signal to embed the field you need (here, `segment`).

</details>

### Running revenue total
<!-- id: running-total-window | dataset: shop | level: Hard | tags: $setWindowFields, running total | order: strict -->

Monthly delivered revenue for 2025 and its running total, using `$setWindowFields`.

Return `{ _id: "YYYY-MM", revenue, running_total }` (both rounded to 2 decimals), in calendar order.

<details>
<summary>Solution</summary>

```js
db.orders.aggregate([
  { $match: { status: "delivered",
              ordered_at: { $gte: ISODate("2025-01-01"), $lt: ISODate("2026-01-01") } } },
  { $group: { _id: { $dateToString: { format: "%Y-%m", date: "$ordered_at" } }, revenue: { $sum: "$total" } } },
  { $setWindowFields: { sortBy: { _id: 1 },
      output: { running_total: { $sum: "$revenue", window: { documents: ["unbounded", "current"] } } } } },
  { $set: { revenue: { $round: ["$revenue", 2] }, running_total: { $round: ["$running_total", 2] } } },
  { $sort: { _id: 1 } }
])
```

`$setWindowFields` is the aggregation framework's window function: `documents: ["unbounded",
"current"]` is SQL's `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`.

</details>

### Most used coupons
<!-- id: coupon-sortbycount | dataset: shop | level: Easy | tags: $sortByCount | order: strict -->

Which coupon codes are used most? Ignore orders without a coupon.

Return `{ _id: <coupon>, count }`, most used first.

<details>
<summary>Solution</summary>

```js
db.orders.aggregate([
  { $match: { coupon: { $exists: true } } },
  { $sortByCount: "$coupon" }
])
```

`$sortByCount` is shorthand for `$group` by the value with a count, then `$sort` descending.

</details>

### Free shipping share
<!-- id: free-shipping-cond | dataset: shop | level: Medium | tags: $cond, $group | order: strict -->

Label each order `"free"` if its shipping fee is 0, else `"paid"`, and count each label.

Return `{ _id: "free" | "paid", orders }`, sorted by `_id`.

<details>
<summary>Solution</summary>

```js
db.orders.aggregate([
  { $group: { _id: { $cond: [{ $eq: ["$shipping.fee", 0] }, "free", "paid"] }, orders: { $sum: 1 } } },
  { $sort: { _id: 1 } }
])
```

</details>

### Days to deliver
<!-- id: days-to-deliver | dataset: shop | level: Hard | tags: $filter, $arrayElemAt, $dateDiff | order: strict -->

Each delivered order's `status_history` has a `delivered` entry. Compute the average number of
days from `ordered_at` to delivery, per shipping country, for countries with at least 100
delivered orders.

Return `{ _id: <country>, orders, avg_days }` with `avg_days` rounded to 1 decimal, slowest first.

> **Hint:** Pull the delivered entry out with `$arrayElemAt` + `$filter`, then `$dateDiff` with
> `unit: "hour"` and divide by 24.

<details>
<summary>Solution</summary>

```js
db.orders.aggregate([
  { $match: { status: "delivered" } },
  { $set: { delivered: { $arrayElemAt: [
      { $filter: { input: "$status_history", cond: { $eq: ["$$this.status", "delivered"] } } }, 0] } } },
  { $group: { _id: "$shipping.country", orders: { $sum: 1 },
              avg_days: { $avg: { $divide: [
                { $dateDiff: { startDate: "$ordered_at", endDate: "$delivered.at", unit: "hour" } }, 24] } } } },
  { $match: { orders: { $gte: 100 } } },
  { $set: { avg_days: { $round: ["$avg_days", 1] } } },
  { $sort: { avg_days: -1, _id: 1 } }
])
```

The same question as the SQL lab's "Delivery time by country": there the delivery time is a
column, here it's an event inside an embedded array. Both are valid models; they make different
queries easy.

</details>

### Biggest city in each country
<!-- id: top-city-per-country | dataset: shop | level: Hard | tags: $group twice, top 1 per group | order: strict -->

For each country, which city has the most customers?

Return `{ _id: <country>, city, customers }`, sorted by `customers` descending then `_id`. Break
ties between cities by city name.

<details>
<summary>Solution</summary>

```js
db.customers.aggregate([
  { $group: { _id: { country: "$address.country", city: "$address.city" }, customers: { $sum: 1 } } },
  { $sort: { customers: -1, "_id.city": 1 } },
  { $group: { _id: "$_id.country", city: { $first: "$_id.city" }, customers: { $first: "$customers" } } },
  { $sort: { customers: -1, _id: 1 } }
])
```

"Top 1 per group" in MongoDB: sort, then `$group` with `$first`. The sort must come before the
second `$group`, which keeps the first document it sees per group.

</details>

### Catalogue by top-level category
<!-- id: products-by-top-category | dataset: shop | level: Medium | tags: $arrayElemAt, $group | order: strict -->

How many products, and at what average price, in each top-level category (the first element of
`category`)?

Return `{ _id: <category>, products, avg_price }` with `avg_price` rounded to 2 decimals, sorted by
`_id`.

<details>
<summary>Solution</summary>

```js
db.products.aggregate([
  { $group: { _id: { $arrayElemAt: ["$category", 0] }, products: { $sum: 1 }, avg_price: { $avg: "$price" } } },
  { $set: { avg_price: { $round: ["$avg_price", 2] } } },
  { $sort: { _id: 1 } }
])
```

Storing the category path as an array makes "everything under Electronics" a simple equality
query, while `$arrayElemAt` reads any level.

</details>

## Writing data

Each attempt runs on a fresh copy of the data, so you can't break anything.

### Restock a product
<!-- id: restock-inc | dataset: shop | level: Easy | tags: updateOne, $inc | order: any -->

A delivery of 50 units arrived for product **101**. Increase its stock atomically.

The checker then reads `{ _id, stock }` of product 101.

<details>
<summary>Solution</summary>

```js
db.products.updateOne({ _id: 101 }, { $inc: { stock: 50 } })
```

`$inc` is atomic on the server: two concurrent restocks both land. Reading the stock, adding 50
in your app and writing it back loses one of them (the classic lost update).

```js verify
db.products.findOne({ _id: 101 }, { stock: 1 })
```

</details>

### Deactivate out-of-stock products
<!-- id: deactivate-out-of-stock | dataset: shop | level: Easy | tags: updateMany, $set | order: any -->

Set `active: false` on every product whose `stock` is 0.

The checker then counts inactive products.

<details>
<summary>Solution</summary>

```js
db.products.updateMany({ stock: 0 }, { $set: { active: false } })
```

```js verify
db.products.countDocuments({ active: false })
```

</details>

### Mark an order as returned
<!-- id: return-order-push | dataset: shop | level: Medium | tags: updateOne, $set, $push | order: any -->

Order **10001** was returned on `2026-01-02`. In one update, set its `status` to `"returned"` and
append `{ status: "returned", at: ISODate("2026-01-02") }` to its `status_history`.

The checker then reads `{ _id, status, status_history }` of order 10001.

<details>
<summary>Solution</summary>

```js
db.orders.updateOne(
  { _id: 10001 },
  { $set: { status: "returned" },
    $push: { status_history: { status: "returned", at: ISODate("2026-01-02") } } }
)
```

Both changes happen atomically because they are in one document. That's the main reason to
embed data that changes together.

```js verify
db.orders.findOne({ _id: 10001 }, { status: 1, status_history: 1 })
```

</details>

### Save to a wishlist (upsert)
<!-- id: wishlist-upsert | dataset: shop | level: Medium | tags: upsert, $addToSet | order: any -->

Customer **5** adds product **101** to their wishlist. Wishlists live in a `wishlists` collection
with one document per customer: `{ customer_id, products: [...] }`. The document may not exist
yet, and adding the same product twice must not duplicate it.

The checker then reads `{ customer_id, products }` from `wishlists` for customer 5 (without `_id`).

<details>
<summary>Solution</summary>

```js
db.wishlists.updateOne(
  { customer_id: 5 },
  { $addToSet: { products: 101 } },
  { upsert: true }
)
```

`upsert: true` inserts the document when nothing matches, using the filter's equality fields
(`customer_id: 5`) as its starting point. `$addToSet` only adds the value if it's absent, so
running this twice is safe (the update is idempotent).

```js verify
db.wishlists.findOne({ customer_id: 5 }, { _id: 0, customer_id: 1, products: 1 })
```

</details>

### Remove a tag
<!-- id: pull-tag | dataset: shop | level: Easy | tags: $pull, arrays | order: any -->

Remove the tag `"bestseller"` from every product that has it.

The checker then counts products still tagged `"bestseller"`. (It should be zero.)

<details>
<summary>Solution</summary>

```js
db.products.updateMany({ tags: "bestseller" }, { $pull: { tags: "bestseller" } })
```

```js verify
db.products.countDocuments({ tags: "bestseller" })
```

</details>

### Delete old reviews
<!-- id: delete-old-reviews | dataset: shop | level: Easy | tags: deleteMany | order: any -->

Delete every review created before **1 July 2024**.

The checker then counts the reviews left.

<details>
<summary>Solution</summary>

```js
db.reviews.deleteMany({ created_at: { $lt: ISODate("2024-07-01") } })
```

Before a bulk delete in production, run the same filter with `countDocuments` to see how many
documents it will remove.

```js verify
db.reviews.countDocuments()
```

</details>

### Insert a new product
<!-- id: insert-product | dataset: shop | level: Easy | tags: insertOne | order: any -->

Add product `_id: 500`: `name` "Lumen Desk Lamp", `brand` "Lumen", `category`
`["Home & Kitchen", "Decor"]`, `price` 39.99, `stock` 120, `active` true, `tags` `["home-kitchen", "lumen"]`.

The checker then reads `{ _id, name, brand, price }` for every product of brand `"Lumen"`, by `_id`.

<details>
<summary>Solution</summary>

```js
db.products.insertOne({
  _id: 500, name: "Lumen Desk Lamp", brand: "Lumen",
  category: ["Home & Kitchen", "Decor"], price: 39.99, stock: 120,
  active: true, tags: ["home-kitchen", "lumen"]
})
```

```js verify
db.products.find({ brand: "Lumen" }, { name: 1, brand: 1, price: 1 }).sort({ _id: 1 })
```

</details>

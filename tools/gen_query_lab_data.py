#!/usr/bin/env python3
"""Generate the Query Lab datasets: realistic, deterministic, license-free.

    python3 tools/gen_query_lab_data.py

Writes (and overwrites):
    SQL/lab/datasets/shop.sql          e-commerce: customers, categories, products, orders, items, payments, reviews
    SQL/lab/datasets/hr.sql            a company: departments, employees (org chart), salary history, projects, applications
    SQL/lab/datasets/analytics.sql     a SaaS product: users, events, subscriptions, an A/B experiment
    NoSQL/lab/datasets/mongodb/*.json  the shop data as documents (orders embed their items)
    NoSQL/lab/datasets/redis/seed.redis  caches, leaderboards, sessions, counters, bitmaps, geo, streams

Every file is plain text a real database loads as is (psql -f, mongoimport --jsonArray,
redis-cli < seed.redis), and the in-browser Query Lab loads the same files. A fixed seed
makes the output byte-identical on every run, so question answers never drift.

Names, cities and coordinates are real-world; companies, brands and people are invented.
Standard library only.
"""
from __future__ import annotations

import json
import math
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SQL_OUT = ROOT / "SQL" / "lab" / "datasets"
NOSQL_OUT = ROOT / "NoSQL" / "lab" / "datasets"
SEED = 20260105

# --------------------------------------------------------------------------- reference data
# (city, region, country, longitude, latitude)
CITIES = [
    ("Mumbai", "Maharashtra", "India", 72.8777, 19.0760), ("Bengaluru", "Karnataka", "India", 77.5946, 12.9716),
    ("Delhi", "Delhi", "India", 77.2090, 28.6139), ("Pune", "Maharashtra", "India", 73.8567, 18.5204),
    ("Hyderabad", "Telangana", "India", 78.4867, 17.3850), ("Chennai", "Tamil Nadu", "India", 80.2707, 13.0827),
    ("New York", "New York", "United States", -74.0060, 40.7128), ("San Francisco", "California", "United States", -122.4194, 37.7749),
    ("Austin", "Texas", "United States", -97.7431, 30.2672), ("Seattle", "Washington", "United States", -122.3321, 47.6062),
    ("Chicago", "Illinois", "United States", -87.6298, 41.8781), ("Boston", "Massachusetts", "United States", -71.0589, 42.3601),
    ("London", "England", "United Kingdom", -0.1276, 51.5072), ("Manchester", "England", "United Kingdom", -2.2426, 53.4808),
    ("Edinburgh", "Scotland", "United Kingdom", -3.1883, 55.9533), ("Berlin", "Berlin", "Germany", 13.4050, 52.5200),
    ("Munich", "Bavaria", "Germany", 11.5820, 48.1351), ("Paris", "Ile-de-France", "France", 2.3522, 48.8566),
    ("Lyon", "Auvergne-Rhone-Alpes", "France", 4.8357, 45.7640), ("Amsterdam", "North Holland", "Netherlands", 4.9041, 52.3676),
    ("Madrid", "Madrid", "Spain", -3.7038, 40.4168), ("Barcelona", "Catalonia", "Spain", 2.1734, 41.3851),
    ("Toronto", "Ontario", "Canada", -79.3832, 43.6532), ("Vancouver", "British Columbia", "Canada", -123.1207, 49.2827),
    ("Sao Paulo", "Sao Paulo", "Brazil", -46.6333, -23.5505), ("Mexico City", "CDMX", "Mexico", -99.1332, 19.4326),
    ("Tokyo", "Tokyo", "Japan", 139.6917, 35.6895), ("Osaka", "Osaka", "Japan", 135.5023, 34.6937),
    ("Singapore", "Singapore", "Singapore", 103.8198, 1.3521), ("Dubai", "Dubai", "United Arab Emirates", 55.2708, 25.2048),
    ("Sydney", "New South Wales", "Australia", 151.2093, -33.8688), ("Melbourne", "Victoria", "Australia", 144.9631, -37.8136),
    ("Nairobi", "Nairobi", "Kenya", 36.8219, -1.2921), ("Lagos", "Lagos", "Nigeria", 3.3792, 6.5244),
    ("Cape Town", "Western Cape", "South Africa", 18.4241, -33.9249), ("Seoul", "Seoul", "South Korea", 126.9780, 37.5665),
]
# Customers cluster where the business is big: India, US, UK first.
CITY_WEIGHTS = [9, 9, 8, 6, 6, 5, 7, 6, 4, 4, 4, 3, 7, 3, 2, 4, 3, 4, 2, 3, 3, 2, 3, 2, 3, 2, 3, 2, 3, 3, 3, 2, 2, 2, 1, 2]

FIRST = """Aarav Aditi Arjun Ananya Rohan Priya Vikram Neha Kabir Isha Rahul Sneha Karan Diya Siddharth Meera Aditya Kavya
Ishaan Tara Liam Olivia Noah Emma James Ava Lucas Sophia Mason Mia Ethan Amelia Logan Harper Jacob Ella Daniel Grace
Henry Chloe Samuel Zoe Oliver Lily Jack Ruby George Freya Leo Isla Hugo Clara Felix Lena Jonas Anna Lukas Marie Elias
Sofia Mateo Valentina Diego Camila Javier Lucia Pablo Elena Gabriel Beatriz Rafael Mariana Thiago Larissa Yuki Haruto
Sakura Ren Aoi Min-jun Ji-woo Seo-yeon Wei Mei Jun Lin Chen Amara Kwame Zainab Chidi Ngozi Tunde Wanjiru Omar Fatima
Yusuf Layla Hassan Noor Ali Aisha Ibrahim Sara Mohammed Leila Ravi Pooja Nikhil Shreya Varun Anjali Manish Rhea""".split()
LAST = """Sharma Patel Iyer Reddy Nair Gupta Mehta Rao Kapoor Singh Joshi Desai Banerjee Chopra Malhotra Menon Pillai Verma
Smith Johnson Williams Brown Jones Garcia Miller Davis Wilson Anderson Taylor Thomas Moore Martin Jackson White Harris
Clark Lewis Walker Hall Young King Wright Scott Green Baker Adams Nelson Carter Mitchell Roberts Turner Phillips Evans
Muller Schmidt Schneider Fischer Weber Becker Wagner Dubois Martin Bernard Laurent Moreau Garcia Fernandez Lopez Martinez
Rodriguez Sanchez Perez Silva Santos Oliveira Costa Souza Tanaka Suzuki Takahashi Watanabe Kim Lee Park Choi Wang Zhang
Liu Chen Okafor Mensah Adeyemi Kamau Otieno Hassan Khan Ahmed Rahman Haddad Nasser Kowalski Novak Jansen De Vries""".split()

T0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
T_END = datetime(2025, 12, 31, 23, 59, tzinfo=timezone.utc)


# --------------------------------------------------------------------------- helpers
def sql_lit(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int,)):
        return str(v)
    if isinstance(v, float):
        return f"{v:.2f}"
    if isinstance(v, datetime):
        return "'" + v.strftime("%Y-%m-%d %H:%M:%S+00") + "'"
    if isinstance(v, date):
        return "'" + v.isoformat() + "'"
    if isinstance(v, (dict, list)):
        return "'" + json.dumps(v, separators=(", ", ": ")).replace("'", "''") + "'"
    return "'" + str(v).replace("'", "''") + "'"


def inserts(table: str, cols: list[str], rows: list[tuple], batch: int = 400) -> str:
    out = []
    for i in range(0, len(rows), batch):
        chunk = rows[i:i + batch]
        vals = ",\n".join("  (" + ", ".join(sql_lit(v) for v in r) + ")" for r in chunk)
        out.append(f"INSERT INTO {table} ({', '.join(cols)}) VALUES\n{vals};")
    return "\n".join(out)


def money(x: float) -> float:
    return round(x + 1e-9, 2)


def slug(s: str) -> str:
    return "".join(c.lower() if c.isalnum() else "." for c in s).strip(".")


def rand_dt(rng: random.Random, start: datetime, end: datetime) -> datetime:
    span = int((end - start).total_seconds())
    return (start + timedelta(seconds=rng.randrange(span))).replace(second=0, microsecond=0)


def header(name: str, blurb: str, tables: str) -> str:
    return f"""-- ============================================================================
-- Query Lab dataset: {name}
-- {blurb}
--
-- Generated by tools/gen_query_lab_data.py (deterministic; do not edit by hand).
-- Load into the lab Postgres:   psql "postgresql://dsa:dsa@localhost:5544/dsa" -f SQL/lab/datasets/{name}.sql
-- Then:                         SET search_path TO {name};
-- Tables: {tables}
-- ============================================================================
DROP SCHEMA IF EXISTS {name} CASCADE;
CREATE SCHEMA {name};
SET search_path TO {name};
"""


def person(rng: random.Random, used: set[str], domain: str) -> tuple[str, str, str]:
    while True:
        f, l = rng.choice(FIRST), rng.choice(LAST)
        email = f"{slug(f)}.{slug(l)}@{domain}"
        n = 2
        while email in used:
            email = f"{slug(f)}.{slug(l)}{n}@{domain}"
            n += 1
        used.add(email)
        return f, l, email


# --------------------------------------------------------------------------- shop
CATEGORY_TREE = {
    "Electronics": {"Phones": {}, "Laptops": {}, "Audio": {"Headphones": {}, "Speakers": {}}, "Wearables": {}, "Accessories": {}},
    "Home & Kitchen": {"Cookware": {}, "Appliances": {}, "Furniture": {}, "Decor": {}},
    "Fashion": {"Men": {}, "Women": {}, "Shoes": {}, "Bags": {}},
    "Books": {"Fiction": {}, "Non-fiction": {}, "Technology": {}},
    "Sports & Outdoors": {"Fitness": {}, "Camping": {}, "Cycling": {}},
    "Beauty": {"Skincare": {}, "Haircare": {}},
    "Grocery": {"Coffee & Tea": {}, "Snacks": {}},
}
# leaf -> (brands, product nouns, price range, attribute maker)
LEAF_SPEC = {
    "Phones": (["Nimbus", "Orbit", "Volt"], ["Smartphone 5G", "Phone Lite", "Phone Pro Max", "Foldable Phone"], (199, 1299)),
    "Laptops": (["Vertex", "Nimbus", "Quanta"], ["Ultrabook 14", "Laptop 15 Pro", "Gaming Laptop 16", "Chromebook 13"], (349, 2499)),
    "Headphones": (["Sonora", "Echo Labs"], ["Wireless Earbuds", "Noise-Cancelling Headphones", "Sport Earbuds"], (29, 399)),
    "Speakers": (["Sonora", "Boomly"], ["Bluetooth Speaker", "Smart Speaker", "Soundbar"], (39, 599)),
    "Wearables": (["Pulse", "Orbit"], ["Fitness Band", "Smartwatch", "Smart Ring"], (49, 499)),
    "Accessories": (["Volt", "Linkr"], ["USB-C Charger 65W", "Power Bank 20000mAh", "Phone Case", "USB-C Hub"], (9, 89)),
    "Cookware": (["Hearth", "Copperline"], ["Cast Iron Skillet", "Non-stick Pan Set", "Dutch Oven", "Chef Knife"], (19, 249)),
    "Appliances": (["Brewmaster", "Kitchenly"], ["Espresso Machine", "Air Fryer", "Blender", "Electric Kettle"], (29, 699)),
    "Furniture": (["Oakhaus", "Nordform"], ["Standing Desk", "Ergonomic Chair", "Bookshelf", "Coffee Table"], (79, 899)),
    "Decor": (["Nordform", "Lumi"], ["Table Lamp", "Wall Clock", "Throw Blanket", "Ceramic Vase"], (15, 149)),
    "Men": (["Northpeak", "Urbane"], ["Merino Sweater", "Chino Trousers", "Oxford Shirt", "Rain Jacket"], (25, 229)),
    "Women": (["Urbane", "Seren"], ["Linen Dress", "Wool Coat", "Silk Blouse", "Denim Jacket"], (29, 299)),
    "Shoes": (["Stride", "Northpeak"], ["Running Shoes", "Leather Sneakers", "Hiking Boots", "Sandals"], (35, 249)),
    "Bags": (["Carryall", "Seren"], ["Laptop Backpack", "Duffel Bag", "Tote Bag", "Crossbody Bag"], (25, 199)),
    "Fiction": (["Paperleaf"], ["The Quiet Harbor", "Midnight Orchard", "The Last Cartographer", "Salt and Silver"], (9, 29)),
    "Non-fiction": (["Paperleaf"], ["Deep Habits", "The Curious Economy", "A Short History of Maps", "Mind the Data"], (12, 35)),
    "Technology": (["Bytebooks"], ["Designing Data Systems", "Practical SQL", "Go in Production", "Python Patterns"], (25, 69)),
    "Fitness": (["Kinetic", "Pulse"], ["Yoga Mat", "Adjustable Dumbbells", "Resistance Bands", "Foam Roller"], (15, 349)),
    "Camping": (["Northpeak", "Trailhead"], ["2-Person Tent", "Sleeping Bag", "Camping Stove", "Headlamp"], (19, 399)),
    "Cycling": (["Velo", "Trailhead"], ["Bike Helmet", "Bike Lights Set", "Cycling Gloves", "Bike Lock"], (15, 179)),
    "Skincare": (["Dewdrop", "Botanika"], ["Vitamin C Serum", "Daily Moisturizer", "Sunscreen SPF 50", "Cleansing Gel"], (9, 69)),
    "Haircare": (["Botanika"], ["Argan Shampoo", "Repair Conditioner", "Hair Dryer", "Styling Cream"], (8, 149)),
    "Coffee & Tea": (["Highland Roast", "Leafworks"], ["Single-Origin Beans 1kg", "Green Tea 100 bags", "Cold Brew Pack", "Masala Chai"], (7, 49)),
    "Snacks": (["Crunchwell"], ["Trail Mix", "Dark Chocolate Bar", "Protein Bar Box", "Salted Almonds"], (3, 29)),
}
COLORS = ["Black", "White", "Silver", "Blue", "Green", "Red", "Graphite", "Sand", "Navy", "Olive"]


def attributes_for(rng: random.Random, leaf: str, top: str) -> dict:
    if leaf in ("Phones",):
        return {"color": rng.choice(COLORS), "storage_gb": rng.choice([64, 128, 256, 512]), "screen_in": rng.choice([6.1, 6.4, 6.7]), "5g": True}
    if leaf == "Laptops":
        return {"color": rng.choice(["Silver", "Graphite", "Black"]), "ram_gb": rng.choice([8, 16, 32]), "storage_gb": rng.choice([256, 512, 1024]), "cpu": rng.choice(["8-core", "10-core", "12-core"])}
    if top == "Electronics":
        return {"color": rng.choice(COLORS), "wireless": rng.random() < 0.8, "battery_hours": rng.choice([8, 12, 20, 30, 40])}
    if top == "Fashion":
        return {"color": rng.choice(COLORS), "sizes": rng.sample(["XS", "S", "M", "L", "XL"], rng.randint(2, 5)), "material": rng.choice(["cotton", "wool", "linen", "leather", "polyester"])}
    if top == "Books":
        return {"format": rng.choice(["paperback", "hardcover", "ebook"]), "pages": rng.randint(180, 720), "language": rng.choice(["English", "English", "English", "Spanish", "German"])}
    if top == "Grocery":
        return {"weight_g": rng.choice([100, 250, 500, 1000]), "organic": rng.random() < 0.4}
    return {"color": rng.choice(COLORS), "weight_kg": round(rng.uniform(0.2, 25), 1)}


def gen_shop(rng: random.Random) -> dict:
    # categories (3 levels)
    categories = []

    def walk(tree, parent):
        for name, sub in tree.items():
            cid = len(categories) + 1
            categories.append((cid, name, parent))
            walk(sub, cid)
    walk(CATEGORY_TREE, None)
    cat_by_name = {c[1]: c for c in categories}
    top_of = {}
    for cid, name, parent in categories:
        p = parent
        top = name
        while p is not None:
            pc = categories[p - 1]
            top, p = pc[1], pc[2]
        top_of[name] = top

    # products
    products = []
    pid = 100
    for leaf, (brands, nouns, (lo, hi)) in LEAF_SPEC.items():
        for noun in nouns:
            for brand in rng.sample(brands, min(len(brands), rng.choice([1, 2, 2]))):
                pid += 1
                price = money(rng.uniform(lo, hi))
                price = math.floor(price) + rng.choice([0.0, 0.49, 0.99, 0.99])  # $x.99 pricing
                cost = money(price * rng.uniform(0.42, 0.72))
                launched = date(2022, 1, 1) + timedelta(days=rng.randrange(0, 1260))
                name = noun if leaf in ("Fiction", "Non-fiction", "Technology") else f"{brand} {noun}"
                products.append({
                    "product_id": pid, "sku": f"{slug(brand)[:3].upper()}-{pid}", "name": name, "brand": brand,
                    "category_id": cat_by_name[leaf][0], "category": leaf, "top": top_of[leaf],
                    "price": money(price), "cost": cost, "stock": rng.choice([0, 0, rng.randint(1, 15)] + [rng.randint(20, 500)] * 6),
                    "attributes": attributes_for(rng, leaf, top_of[leaf]), "launched_at": launched,
                    "is_active": rng.random() > 0.06,
                })
    # popularity: a few hits, a long tail, a handful never sold
    pop = [rng.paretovariate(1.3) for _ in products]
    for i in rng.sample(range(len(products)), 6):
        pop[i] = 0.0

    # customers
    used = set()
    customers = []
    for cid in range(1, 2001):
        f, l, email = person(rng, used, rng.choice(["gmail.com", "outlook.com", "yahoo.com", "proton.me", "icloud.com"]))
        city = rng.choices(CITIES, CITY_WEIGHTS)[0]
        signup = rand_dt(rng, datetime(2022, 6, 1, tzinfo=timezone.utc), datetime(2025, 11, 30, tzinfo=timezone.utc))
        customers.append({
            "customer_id": cid, "first_name": f, "last_name": l, "email": email,
            "phone": None if rng.random() < 0.12 else f"+{rng.randint(1, 99)}-{rng.randint(200, 999)}-{rng.randint(1000000, 9999999)}",
            "city": city[0], "region": city[1], "country": city[2], "lon": city[3], "lat": city[4],
            "signup_at": signup, "referred_by": None, "segment": rng.choices(["consumer", "consumer", "business", "vip"], [55, 25, 15, 5])[0],
            "marketing_opt_in": rng.random() < 0.55,
        })
    for c in customers:
        if rng.random() < 0.18:
            ref = rng.choice(customers)
            if ref["customer_id"] != c["customer_id"] and ref["signup_at"] < c["signup_at"]:
                c["referred_by"] = ref["customer_id"]
    # heavy buyers: Pareto weights; 8% never order at all
    buy_w = [0.0 if rng.random() < 0.08 else min(rng.paretovariate(1.6), 6.0) for _ in customers]

    # orders with seasonality (Nov/Dec peak, weekend bump) and growth over time
    orders, items, payments = [], [], []
    oid, pay_id = 10000, 1
    day = T0
    coupons = ["WELCOME10", "FESTIVE20", "SUMMER15", None, None, None, None, None, None, None]
    while day <= T_END:
        month_factor = {11: 1.8, 12: 2.1, 1: 0.8, 7: 1.15}.get(day.month, 1.0)
        growth = 1 + (day - T0).days / 730 * 0.6
        weekend = 1.25 if day.weekday() >= 5 else 1.0
        n = int(rng.gauss(5.2 * month_factor * growth * weekend, 1.6))
        for _ in range(max(n, 0)):
            cust = rng.choices(customers, buy_w)[0]
            placed = day + timedelta(minutes=rng.randrange(7 * 60, 24 * 60 - 1))
            if placed < cust["signup_at"]:
                continue
            oid += 1
            status = rng.choices(["delivered", "shipped", "placed", "cancelled", "returned"], [78, 5, 3, 8, 6])[0]
            if placed > T_END - timedelta(days=4) and status == "delivered":
                status = rng.choice(["placed", "shipped"])
            ship_city = cust if rng.random() > 0.07 else {**cust, **dict(zip(["city", "region", "country"], rng.choices(CITIES, CITY_WEIGHTS)[0][:3]))}
            coupon = rng.choice(coupons) if not (day.month in (11, 12)) else rng.choice(["FESTIVE20", None, None, "WELCOME10"])
            n_lines = rng.choices([1, 2, 3, 4, 5], [48, 27, 14, 7, 4])[0]
            chosen = []
            while len(chosen) < n_lines:
                p = rng.choices(products, pop)[0]
                if p not in chosen and p["launched_at"] <= placed.date():
                    chosen.append(p)
                if len(chosen) == 0 and rng.random() < 0.01:
                    break
            if not chosen:
                oid -= 1
                continue
            total = 0.0
            for line, p in enumerate(chosen, 1):
                qty = rng.choices([1, 2, 3, 4], [72, 18, 7, 3])[0]
                unit = money(p["price"] * rng.choice([1, 1, 1, 1, 0.95, 0.9, 1.05]))
                disc = rng.choices([0, 5, 10, 20], [70, 12, 12, 6])[0]
                items.append({"order_id": oid, "line_no": line, "product_id": p["product_id"], "quantity": qty, "unit_price": unit, "discount_pct": disc})
                total += qty * unit * (1 - disc / 100)
            shipping = 0.0 if total >= 50 else 4.99
            total = money(total + shipping)
            method = rng.choices(["card", "upi", "paypal", "wallet", "cod"], [45, 20, 15, 10, 10])[0]
            delivered_at = placed + timedelta(days=rng.randint(1, 9), hours=rng.randint(0, 20)) if status in ("delivered", "returned") else None
            orders.append({"order_id": oid, "customer_id": cust["customer_id"], "ordered_at": placed, "status": status,
                           "ship_city": ship_city["city"], "ship_country": ship_city["country"], "payment_method": method,
                           "coupon_code": coupon, "shipping_fee": shipping, "total_amount": total, "delivered_at": delivered_at})
            pstat = "refunded" if status in ("cancelled", "returned") else ("pending" if method == "cod" and status != "delivered" else "captured")
            if rng.random() < 0.04 and total > 60:     # split payment: wallet + card
                part = money(total * rng.uniform(0.2, 0.5))
                payments.append({"payment_id": pay_id, "order_id": oid, "method": "wallet", "amount": part, "status": pstat, "paid_at": placed + timedelta(minutes=1)}); pay_id += 1
                payments.append({"payment_id": pay_id, "order_id": oid, "method": method, "amount": money(total - part), "status": pstat, "paid_at": placed + timedelta(minutes=2)}); pay_id += 1
            elif rng.random() < 0.006:                 # a few payments that do not match the order total (data-quality question)
                payments.append({"payment_id": pay_id, "order_id": oid, "method": method, "amount": money(total - rng.choice([1, 5, 10])), "status": pstat, "paid_at": placed + timedelta(minutes=1)}); pay_id += 1
            elif not (status == "cancelled" and rng.random() < 0.5):
                payments.append({"payment_id": pay_id, "order_id": oid, "method": method, "amount": total, "status": pstat, "paid_at": placed + timedelta(minutes=1)}); pay_id += 1
        day += timedelta(days=1)

    # reviews: by buyers of delivered orders, skewed positive
    bought = {}
    for it in items:
        bought.setdefault(it["order_id"], []).append(it["product_id"])
    reviews, seen = [], set()
    titles = {5: ["Love it", "Exactly as described", "Best purchase this year", "Excellent quality"],
              4: ["Very good", "Solid value", "Happy with it", "Works well"],
              3: ["It's okay", "Average", "Does the job", "Mixed feelings"],
              2: ["Disappointed", "Not worth the price", "Stopped working"],
              1: ["Terrible", "Broke in a week", "Do not buy"]}
    rid = 1
    for o in orders:
        if o["status"] != "delivered" or rng.random() > 0.38:
            continue
        for p_id in bought[o["order_id"]]:
            key = (o["customer_id"], p_id)
            if key in seen or rng.random() > 0.75:
                continue
            seen.add(key)
            rating = rng.choices([5, 4, 3, 2, 1], [46, 30, 12, 7, 5])[0]
            reviews.append({"review_id": rid, "product_id": p_id, "customer_id": o["customer_id"], "rating": rating,
                            "title": rng.choice(titles[rating]), "verified_purchase": True,
                            "created_at": o["delivered_at"] + timedelta(days=rng.randint(1, 40)) if o["delivered_at"] else o["ordered_at"]})
            rid += 1
    return {"categories": categories, "products": products, "customers": customers, "orders": orders,
            "items": items, "payments": payments, "reviews": reviews}


def shop_sql(d: dict) -> str:
    s = [header("shop", "An online store: 2 years of orders (2024-2025) with seasonality, returns and reviews.",
                "customers, categories, products, orders, order_items, payments, reviews")]
    s.append("""
CREATE TABLE customers (
    customer_id      INT PRIMARY KEY,
    first_name       TEXT NOT NULL,
    last_name        TEXT NOT NULL,
    email            TEXT NOT NULL UNIQUE,
    phone            TEXT,
    city             TEXT NOT NULL,
    region           TEXT NOT NULL,
    country          TEXT NOT NULL,
    signup_at        TIMESTAMPTZ NOT NULL,
    referred_by      INT REFERENCES customers(customer_id),
    segment          TEXT NOT NULL CHECK (segment IN ('consumer', 'business', 'vip')),
    marketing_opt_in BOOLEAN NOT NULL
);
CREATE TABLE categories (
    category_id INT PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    parent_id   INT REFERENCES categories(category_id)
);
CREATE TABLE products (
    product_id  INT PRIMARY KEY,
    sku         TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    brand       TEXT NOT NULL,
    category_id INT NOT NULL REFERENCES categories(category_id),
    price       NUMERIC(10,2) NOT NULL CHECK (price > 0),
    cost        NUMERIC(10,2) NOT NULL,
    stock       INT NOT NULL CHECK (stock >= 0),
    attributes  JSONB NOT NULL DEFAULT '{}',
    launched_at DATE NOT NULL,
    is_active   BOOLEAN NOT NULL
);
CREATE TABLE orders (
    order_id       INT PRIMARY KEY,
    customer_id    INT NOT NULL REFERENCES customers(customer_id),
    ordered_at     TIMESTAMPTZ NOT NULL,
    status         TEXT NOT NULL CHECK (status IN ('placed', 'shipped', 'delivered', 'cancelled', 'returned')),
    ship_city      TEXT NOT NULL,
    ship_country   TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    coupon_code    TEXT,
    shipping_fee   NUMERIC(8,2) NOT NULL,
    total_amount   NUMERIC(10,2) NOT NULL,
    delivered_at   TIMESTAMPTZ
);
CREATE TABLE order_items (
    order_id     INT NOT NULL REFERENCES orders(order_id),
    line_no      INT NOT NULL,
    product_id   INT NOT NULL REFERENCES products(product_id),
    quantity     INT NOT NULL CHECK (quantity > 0),
    unit_price   NUMERIC(10,2) NOT NULL,
    discount_pct INT NOT NULL DEFAULT 0,
    PRIMARY KEY (order_id, line_no)
);
CREATE TABLE payments (
    payment_id INT PRIMARY KEY,
    order_id   INT NOT NULL REFERENCES orders(order_id),
    method     TEXT NOT NULL,
    amount     NUMERIC(10,2) NOT NULL,
    status     TEXT NOT NULL CHECK (status IN ('captured', 'pending', 'refunded')),
    paid_at    TIMESTAMPTZ NOT NULL
);
CREATE TABLE reviews (
    review_id         INT PRIMARY KEY,
    product_id        INT NOT NULL REFERENCES products(product_id),
    customer_id       INT NOT NULL REFERENCES customers(customer_id),
    rating            INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title             TEXT NOT NULL,
    verified_purchase BOOLEAN NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL,
    UNIQUE (customer_id, product_id)
);
""")
    # referrals reference earlier customers only, so insert order is safe
    s.append(inserts("customers", ["customer_id", "first_name", "last_name", "email", "phone", "city", "region", "country",
                                   "signup_at", "referred_by", "segment", "marketing_opt_in"],
                     [tuple(c[k] for k in ["customer_id", "first_name", "last_name", "email", "phone", "city", "region", "country",
                                            "signup_at", "referred_by", "segment", "marketing_opt_in"])
                      for c in sorted(d["customers"], key=lambda c: (c["referred_by"] is not None, c["customer_id"]))]))
    s.append(inserts("categories", ["category_id", "name", "parent_id"], d["categories"]))
    s.append(inserts("products", ["product_id", "sku", "name", "brand", "category_id", "price", "cost", "stock", "attributes", "launched_at", "is_active"],
                     [tuple(p[k] for k in ["product_id", "sku", "name", "brand", "category_id", "price", "cost", "stock", "attributes", "launched_at", "is_active"]) for p in d["products"]]))
    s.append(inserts("orders", ["order_id", "customer_id", "ordered_at", "status", "ship_city", "ship_country", "payment_method", "coupon_code", "shipping_fee", "total_amount", "delivered_at"],
                     [tuple(o[k] for k in ["order_id", "customer_id", "ordered_at", "status", "ship_city", "ship_country", "payment_method", "coupon_code", "shipping_fee", "total_amount", "delivered_at"]) for o in d["orders"]]))
    s.append(inserts("order_items", ["order_id", "line_no", "product_id", "quantity", "unit_price", "discount_pct"],
                     [tuple(i[k] for k in ["order_id", "line_no", "product_id", "quantity", "unit_price", "discount_pct"]) for i in d["items"]]))
    s.append(inserts("payments", ["payment_id", "order_id", "method", "amount", "status", "paid_at"],
                     [tuple(p[k] for k in ["payment_id", "order_id", "method", "amount", "status", "paid_at"]) for p in d["payments"]]))
    s.append(inserts("reviews", ["review_id", "product_id", "customer_id", "rating", "title", "verified_purchase", "created_at"],
                     [tuple(r[k] for k in ["review_id", "product_id", "customer_id", "rating", "title", "verified_purchase", "created_at"]) for r in d["reviews"]]))
    s.append("""
CREATE INDEX ON orders (customer_id);
CREATE INDEX ON orders (ordered_at);
CREATE INDEX ON order_items (product_id);
CREATE INDEX ON reviews (product_id);
ANALYZE;
""")
    return "\n".join(s)


# --------------------------------------------------------------------------- hr
DEPTS = [  # name, city, budget, IC title, IC base salary
    ("Executive", "San Francisco", 3_000_000, "Chief of Staff", 210_000),
    ("Engineering", "Bengaluru", 9_500_000, "Software Engineer", 118_000),
    ("Data Science", "Bengaluru", 3_200_000, "Data Scientist", 122_000),
    ("Product", "San Francisco", 2_800_000, "Product Manager", 135_000),
    ("Design", "London", 1_500_000, "Product Designer", 102_000),
    ("Sales", "New York", 4_100_000, "Account Executive", 84_000),
    ("Marketing", "London", 2_100_000, "Marketing Specialist", 78_000),
    ("Customer Success", "Pune", 1_700_000, "Support Specialist", 52_000),
    ("Finance", "New York", 1_400_000, "Financial Analyst", 92_000),
    ("People", "Berlin", 1_100_000, "HR Business Partner", 81_000),
    ("Legal", "London", 1_200_000, "Counsel", 140_000),
    ("Research Lab", "Toronto", 900_000, "Research Scientist", 150_000),   # new team, nobody hired yet
]
CITY_ROW = {c[0]: c for c in CITIES}


def gen_hr(rng: random.Random) -> dict:
    used = set()
    departments = [(i + 1, d[0], d[1], CITY_ROW[d[1]][2], d[2]) for i, d in enumerate(DEPTS)]
    emps = []
    eid = 1000

    def add(first, last, email, title, dept_id, mgr, salary, hire, level, city):
        nonlocal eid
        eid += 1
        emps.append({"emp_id": eid, "first_name": first, "last_name": last, "email": email, "job_title": title, "dept_id": dept_id,
                     "manager_id": mgr, "salary": salary, "hire_date": hire, "level": level, "city": city[0], "country": city[2],
                     "commission_pct": None, "termination_date": None,
                     "birth_date": date(rng.randint(1965, 2001), rng.randint(1, 12), rng.randint(1, 28)), "gender": rng.choice(["F", "M", "F", "M", "X"])})
        return eid

    f, l, e = person(rng, used, "northwind-labs.com")
    ceo = add(f, l, e, "Chief Executive Officer", 1, None, 420_000, date(2015, 3, 2), "C-level", CITY_ROW["San Francisco"])
    for dept_id, name, city, country, budget in departments[1:]:
        if name == "Research Lab":
            continue
        ic_title, base = DEPTS[dept_id - 1][3], DEPTS[dept_id - 1][4]
        f, l, e = person(rng, used, "northwind-labs.com")
        vp_hire = date(2015, 6, 1) + timedelta(days=rng.randrange(0, 1500))
        vp = add(f, l, e, f"VP of {name}", dept_id, ceo, round(base * rng.uniform(2.0, 2.4), -3), vp_hire, "VP", CITY_ROW[city])
        teams = {"Engineering": (6, 7), "Data Science": (2, 3), "Sales": (3, 4), "Customer Success": (3, 4)}.get(name, (1, 2))
        for _ in range(rng.randint(*teams)):
            f, l, e = person(rng, used, "northwind-labs.com")
            m_hire = vp_hire + timedelta(days=rng.randrange(60, 2400))
            mgr = add(f, l, e, f"{name} Manager" if name != "Engineering" else "Engineering Manager", dept_id, vp,
                      round(base * rng.uniform(1.35, 1.6), -3), min(m_hire, date(2024, 6, 1)), "Manager", CITY_ROW[city])
            for _ in range(rng.randint(4, 8)):
                f, l, e = person(rng, used, "northwind-labs.com")
                lvl = rng.choices(["Junior", "Mid", "Senior", "Staff"], [20, 40, 30, 10])[0]
                mult = {"Junior": 0.72, "Mid": 1.0, "Senior": 1.28, "Staff": 1.62}[lvl] * rng.uniform(0.9, 1.12)
                title = {"Junior": f"Junior {ic_title}", "Mid": ic_title, "Senior": f"Senior {ic_title}", "Staff": f"Staff {ic_title}"}[lvl]
                hire = date(2016, 1, 4) + timedelta(days=rng.randrange(0, 3550))
                remote = rng.random() < 0.25
                ec = rng.choices(CITIES, CITY_WEIGHTS)[0] if remote else CITY_ROW[city]
                add(f, l, e, title, dept_id, mgr, round(base * mult, -3), hire, lvl, ec)
    # salary realities: a few ICs out-earn their manager; Sales gets commission; ~12% have left
    by_id = {x["emp_id"]: x for x in emps}
    for x in rng.sample([x for x in emps if x["level"] == "Staff"], 4):
        x["salary"] = by_id[x["manager_id"]]["salary"] + rng.choice([2000, 5000, 9000])
    for x in emps:
        if x["dept_id"] == 6 and x["level"] != "VP":
            x["commission_pct"] = rng.choice([0.05, 0.08, 0.10, 0.12])
        if x["level"] in ("Junior", "Mid", "Senior") and rng.random() < 0.12:
            x["termination_date"] = max(x["hire_date"] + timedelta(days=rng.randint(200, 1500)), date(2020, 1, 1))
            if x["termination_date"] > date(2025, 12, 15):
                x["termination_date"] = None
    # salary history: hire salary grows to today's salary through yearly raises
    hist = []
    for x in emps:
        end = x["termination_date"] or date(2025, 12, 31)
        years = max(1, (end - x["hire_date"]).days // 365)
        steps = [x["hire_date"] + timedelta(days=365 * k + rng.randint(-20, 20)) for k in range(years)]
        steps[0] = x["hire_date"]
        sal = x["salary"]
        sals = [sal]
        for _ in steps[1:]:
            sal = round(sal / rng.uniform(1.03, 1.11), -2)
            sals.append(sal)
        sals.reverse()
        for k, st in enumerate(steps):
            to = steps[k + 1] - timedelta(days=1) if k + 1 < len(steps) else None
            hist.append((x["emp_id"], sals[k], st, to, "hire" if k == 0 else rng.choice(["annual review", "annual review", "promotion", "market adjustment"])))
    # projects and assignments
    names = ["Atlas", "Beacon", "Cobalt", "Delta", "Ember", "Falcon", "Granite", "Helix", "Ion", "Juniper", "Keystone", "Lumen",
             "Monsoon", "Nova", "Onyx", "Polaris", "Quartz", "Raven", "Summit", "Tundra", "Umbra", "Vector", "Willow", "Zephyr"]
    projects = []
    for i, nm in enumerate(names, 1):
        dept = rng.choice(departments[1:11])
        start = date(2022, 1, 1) + timedelta(days=rng.randrange(0, 1200))
        status = rng.choices(["completed", "active", "on_hold", "cancelled"], [40, 40, 10, 10])[0]
        end = start + timedelta(days=rng.randint(60, 540)) if status in ("completed", "cancelled") else None
        projects.append((i, f"Project {nm}", dept[0], start, end, status, round(rng.uniform(80_000, 2_500_000), -3)))
    assign = set()
    rows_assign = []
    actives = [x for x in emps if x["termination_date"] is None and x["level"] not in ("C-level",)]
    for p in projects:
        team = rng.sample([x for x in actives if x["dept_id"] == p[2]] or actives, k=min(rng.randint(3, 8), 8))
        team += rng.sample(actives, rng.randint(0, 3))       # cross-functional members
        for k, x in enumerate(team):
            if (x["emp_id"], p[0]) in assign:
                continue
            assign.add((x["emp_id"], p[0]))
            rows_assign.append((x["emp_id"], p[0], "lead" if k == 0 else rng.choice(["contributor", "contributor", "reviewer"]), rng.choice([4, 8, 12, 16, 20, 40])))
    # job applications, with real-world duplicates (same person applying twice)
    apps = []
    aid = 1
    positions = ["Software Engineer", "Data Scientist", "Product Designer", "Account Executive", "Support Specialist", "Financial Analyst"]
    pool = []
    for _ in range(260):
        f, l, e = person(rng, set(), rng.choice(["gmail.com", "outlook.com", "yahoo.com"]))
        pool.append((f, l, e))
    for f, l, e in pool:
        pos = rng.choice(positions)
        when = datetime(2025, 1, 1, tzinfo=timezone.utc) + timedelta(hours=rng.randrange(0, 8000))
        stage = rng.choices(["applied", "screen", "interview", "offer", "hired", "rejected"], [30, 20, 15, 5, 5, 25])[0]
        apps.append((aid, f"{f} {l}", e, pos, when, rng.choice(["LinkedIn", "Referral", "Careers page", "Job board"]), stage)); aid += 1
        if rng.random() < 0.09:      # duplicate: same email + position, re-submitted later
            apps.append((aid, f"{f} {l}", e.upper() if rng.random() < 0.3 else e, pos, when + timedelta(days=rng.randint(0, 30)), "Careers page", "applied")); aid += 1
    return {"departments": departments, "employees": emps, "salary_history": hist, "projects": projects,
            "employee_projects": rows_assign, "applications": apps}


def hr_sql(d: dict) -> str:
    s = [header("hr", "Northwind Labs, a 200-person tech company: org chart, salaries, history, projects, hiring.",
                "departments, employees, salary_history, projects, employee_projects, job_applications")]
    s.append("""
CREATE TABLE departments (
    dept_id   INT PRIMARY KEY,
    name      TEXT NOT NULL UNIQUE,
    city      TEXT NOT NULL,
    country   TEXT NOT NULL,
    budget    NUMERIC(12,2) NOT NULL
);
CREATE TABLE employees (
    emp_id           INT PRIMARY KEY,
    first_name       TEXT NOT NULL,
    last_name        TEXT NOT NULL,
    email            TEXT NOT NULL UNIQUE,
    job_title        TEXT NOT NULL,
    level            TEXT NOT NULL,
    dept_id          INT NOT NULL REFERENCES departments(dept_id),
    manager_id       INT REFERENCES employees(emp_id),
    salary           NUMERIC(10,2) NOT NULL,
    commission_pct   NUMERIC(4,2),
    hire_date        DATE NOT NULL,
    termination_date DATE,
    birth_date       DATE NOT NULL,
    gender           CHAR(1) NOT NULL,
    city             TEXT NOT NULL,
    country          TEXT NOT NULL
);
CREATE TABLE salary_history (
    emp_id         INT NOT NULL REFERENCES employees(emp_id),
    salary         NUMERIC(10,2) NOT NULL,
    effective_from DATE NOT NULL,
    effective_to   DATE,
    reason         TEXT NOT NULL,
    PRIMARY KEY (emp_id, effective_from)
);
CREATE TABLE projects (
    project_id INT PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE,
    dept_id    INT NOT NULL REFERENCES departments(dept_id),
    start_date DATE NOT NULL,
    end_date   DATE,
    status     TEXT NOT NULL,
    budget     NUMERIC(12,2) NOT NULL
);
CREATE TABLE employee_projects (
    emp_id         INT NOT NULL REFERENCES employees(emp_id),
    project_id     INT NOT NULL REFERENCES projects(project_id),
    role           TEXT NOT NULL,
    hours_per_week INT NOT NULL,
    PRIMARY KEY (emp_id, project_id)
);
CREATE TABLE job_applications (
    application_id INT PRIMARY KEY,
    applicant_name TEXT NOT NULL,
    email          TEXT NOT NULL,
    position       TEXT NOT NULL,
    applied_at     TIMESTAMPTZ NOT NULL,
    source         TEXT NOT NULL,
    stage          TEXT NOT NULL
);
""")
    s.append(inserts("departments", ["dept_id", "name", "city", "country", "budget"], d["departments"]))
    cols = ["emp_id", "first_name", "last_name", "email", "job_title", "level", "dept_id", "manager_id", "salary", "commission_pct",
            "hire_date", "termination_date", "birth_date", "gender", "city", "country"]
    s.append(inserts("employees", cols, [tuple(x[k] for k in cols) for x in d["employees"]]))
    s.append(inserts("salary_history", ["emp_id", "salary", "effective_from", "effective_to", "reason"], d["salary_history"]))
    s.append(inserts("projects", ["project_id", "name", "dept_id", "start_date", "end_date", "status", "budget"], d["projects"]))
    s.append(inserts("employee_projects", ["emp_id", "project_id", "role", "hours_per_week"], d["employee_projects"]))
    s.append(inserts("job_applications", ["application_id", "applicant_name", "email", "position", "applied_at", "source", "stage"], d["applications"]))
    s.append("\nCREATE INDEX ON employees (dept_id);\nCREATE INDEX ON employees (manager_id);\nANALYZE;\n")
    return "\n".join(s)


# --------------------------------------------------------------------------- analytics
def gen_analytics(rng: random.Random) -> dict:
    users, events, subs, exp = [], [], [], []
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    channels = ["organic", "paid_search", "social", "referral", "email"]
    pages = ["/home", "/pricing", "/docs", "/dashboard", "/settings", "/reports", "/integrations"]
    eid = 1
    for uid in range(1, 801):
        signup = rand_dt(rng, start, datetime(2025, 9, 30, tzinfo=timezone.utc))
        ch = rng.choices(channels, [35, 25, 15, 15, 10])[0]
        city = rng.choices(CITIES, CITY_WEIGHTS)[0]
        device = rng.choices(["web", "ios", "android"], [50, 25, 25])[0]
        users.append((uid, signup, ch, city[2], device))
        # engagement: channel quality + random persona; activity decays over time
        stickiness = {"organic": 0.62, "referral": 0.70, "email": 0.55, "paid_search": 0.45, "social": 0.38}[ch] * rng.uniform(0.6, 1.3)
        day = signup.replace(hour=0, minute=0)
        streak_bias = rng.random() < 0.10                     # power users with long daily streaks
        active_days = 0
        while day < datetime(2025, 12, 31, tzinfo=timezone.utc):
            age = (day.date() - signup.date()).days
            p = (0.92 if streak_bias else stickiness) * math.exp(-age / (90 if streak_bias else 25)) + 0.01
            if age == 0 or rng.random() < p:
                active_days += 1
                t = day + timedelta(hours=rng.randint(6, 23), minutes=rng.randint(0, 59))
                if age == 0:
                    t = max(t, signup)
                events.append((eid, uid, "login", t, None, None)); eid += 1
                for _ in range(rng.choice([0, 1, 1, 2])):
                    t += timedelta(minutes=rng.randint(1, 15))
                    events.append((eid, uid, "page_view", t, rng.choice(pages), None)); eid += 1
                if rng.random() < 0.06:
                    t += timedelta(minutes=rng.randint(1, 10))
                    events.append((eid, uid, "upgrade_click", t, "/pricing", None)); eid += 1
            day += timedelta(days=1)
            if active_days > 90:
                break
        # subscriptions: most stay free; some convert, some churn, some upgrade
        if rng.random() < 0.28 and active_days > 3:
            plan = rng.choices(["pro", "team"], [75, 25])[0]
            st = signup + timedelta(days=rng.randint(0, 40))
            mrr = 19.0 if plan == "pro" else 49.0 * rng.choice([1, 2, 3, 5])
            churned = rng.random() < 0.35
            en = st + timedelta(days=rng.randint(30, 300)) if churned else None
            if en and en > datetime(2025, 12, 31, tzinfo=timezone.utc):
                en = None
            subs.append((len(subs) + 1, uid, plan, st, en, mrr))
            if not en and plan == "pro" and rng.random() < 0.15:   # upgrade pro -> team
                up = st + timedelta(days=rng.randint(40, 200))
                if up < datetime(2025, 12, 31, tzinfo=timezone.utc):
                    subs[-1] = (subs[-1][0], uid, plan, st, up, mrr)
                    subs.append((len(subs) + 1, uid, "team", up, None, 98.0))
            pay_t = st
            while pay_t < (subs[-1][4] or datetime(2025, 12, 31, tzinfo=timezone.utc)):
                events.append((eid, uid, "payment", pay_t, None, subs[-1][5])); eid += 1
                pay_t += timedelta(days=30)
        # A/B test on the pricing page (signups after March)
        if signup >= datetime(2025, 3, 1, tzinfo=timezone.utc):
            variant = "B" if rng.random() < 0.5 else "A"
            conv = rng.random() < (0.112 if variant == "B" else 0.087)
            exp.append((uid, "pricing_page_v2", variant, signup, conv))
    events.sort(key=lambda e: (e[3], e[0]))
    events = [(i + 1, *e[1:]) for i, e in enumerate(events)]
    return {"users": users, "events": events, "subscriptions": subs, "experiment": exp}


def analytics_sql(d: dict) -> str:
    s = [header("analytics", "Pulseboard, a SaaS app: signups, daily activity, subscriptions and an A/B test (2025).",
                "users, events, subscriptions, experiment_assignments")]
    s.append("""
CREATE TABLE users (
    user_id     INT PRIMARY KEY,
    signup_at   TIMESTAMPTZ NOT NULL,
    channel     TEXT NOT NULL,
    country     TEXT NOT NULL,
    device      TEXT NOT NULL
);
CREATE TABLE events (
    event_id   BIGINT PRIMARY KEY,
    user_id    INT NOT NULL REFERENCES users(user_id),
    event_type TEXT NOT NULL,
    event_at   TIMESTAMPTZ NOT NULL,
    page       TEXT,
    amount     NUMERIC(10,2)
);
CREATE TABLE subscriptions (
    subscription_id INT PRIMARY KEY,
    user_id         INT NOT NULL REFERENCES users(user_id),
    plan            TEXT NOT NULL,
    started_at      TIMESTAMPTZ NOT NULL,
    ended_at        TIMESTAMPTZ,
    mrr             NUMERIC(10,2) NOT NULL
);
CREATE TABLE experiment_assignments (
    user_id     INT NOT NULL REFERENCES users(user_id),
    experiment  TEXT NOT NULL,
    variant     CHAR(1) NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL,
    converted   BOOLEAN NOT NULL,
    PRIMARY KEY (user_id, experiment)
);
""")
    s.append(inserts("users", ["user_id", "signup_at", "channel", "country", "device"], d["users"]))
    s.append(inserts("events", ["event_id", "user_id", "event_type", "event_at", "page", "amount"], d["events"], batch=800))
    s.append(inserts("subscriptions", ["subscription_id", "user_id", "plan", "started_at", "ended_at", "mrr"], d["subscriptions"]))
    s.append(inserts("experiment_assignments", ["user_id", "experiment", "variant", "assigned_at", "converted"], d["experiment"]))
    s.append("\nCREATE INDEX ON events (user_id, event_at);\nCREATE INDEX ON events (event_type, event_at);\nANALYZE;\n")
    return "\n".join(s)


# --------------------------------------------------------------------------- mongodb
def ejson_date(dt: datetime) -> dict:
    return {"$date": dt.strftime("%Y-%m-%dT%H:%M:%SZ")}


def mongo_docs(shop: dict) -> dict:
    cats = {c[0]: c for c in shop["categories"]}

    def path(cid):
        out = []
        while cid:
            out.append(cats[cid][1])
            cid = cats[cid][2]
        return list(reversed(out))
    rating = {}
    for r in shop["reviews"]:
        rating.setdefault(r["product_id"], []).append(r["rating"])
    products = [{
        "_id": p["product_id"], "sku": p["sku"], "name": p["name"], "brand": p["brand"], "category": path(p["category_id"]),
        "price": p["price"], "stock": p["stock"], "attributes": p["attributes"], "active": p["is_active"],
        "launched_at": ejson_date(datetime.combine(p["launched_at"], datetime.min.time(), tzinfo=timezone.utc)),
        "rating": {"avg": round(sum(rating[p["product_id"]]) / len(rating[p["product_id"]]), 2), "count": len(rating[p["product_id"]])} if p["product_id"] in rating else {"avg": None, "count": 0},
        "tags": sorted({p["top"].lower().replace(" & ", "-").replace(" ", "-"), p["brand"].lower()} | ({"bestseller"} if len(rating.get(p["product_id"], [])) > 25 else set())),
    } for p in shop["products"]]
    cust = {c["customer_id"]: c for c in shop["customers"]}
    customers = [{
        "_id": c["customer_id"], "name": {"first": c["first_name"], "last": c["last_name"]}, "email": c["email"],
        **({"phone": c["phone"]} if c["phone"] else {}),
        "address": {"city": c["city"], "region": c["region"], "country": c["country"], "location": {"type": "Point", "coordinates": [c["lon"], c["lat"]]}},
        "segment": c["segment"], "signed_up": ejson_date(c["signup_at"]), "marketing_opt_in": c["marketing_opt_in"],
        **({"referred_by": c["referred_by"]} if c["referred_by"] else {}),
    } for c in shop["customers"]]
    prod = {p["product_id"]: p for p in shop["products"]}
    items_by = {}
    for it in shop["items"]:
        items_by.setdefault(it["order_id"], []).append(it)
    pay_by = {}
    for pmt in shop["payments"]:
        pay_by.setdefault(pmt["order_id"], []).append(pmt)
    orders = []
    for o in shop["orders"]:
        c = cust[o["customer_id"]]
        hist = [{"status": "placed", "at": ejson_date(o["ordered_at"])}]
        if o["status"] in ("shipped", "delivered", "returned"):
            hist.append({"status": "shipped", "at": ejson_date(o["ordered_at"] + timedelta(days=1))})
        if o["delivered_at"]:
            hist.append({"status": "delivered", "at": ejson_date(o["delivered_at"])})
        if o["status"] in ("cancelled", "returned"):
            hist.append({"status": o["status"], "at": ejson_date((o["delivered_at"] or o["ordered_at"]) + timedelta(days=2))})
        orders.append({
            "_id": o["order_id"],
            "customer": {"_id": c["customer_id"], "name": f"{c['first_name']} {c['last_name']}", "city": c["city"], "country": c["country"]},
            "ordered_at": ejson_date(o["ordered_at"]), "status": o["status"],
            "items": [{"product_id": it["product_id"], "name": prod[it["product_id"]]["name"], "category": prod[it["product_id"]]["category"],
                       "qty": it["quantity"], "price": it["unit_price"], **({"discount_pct": it["discount_pct"]} if it["discount_pct"] else {})}
                      for it in items_by[o["order_id"]]],
            "shipping": {"city": o["ship_city"], "country": o["ship_country"], "fee": o["shipping_fee"]},
            "payment": {"method": o["payment_method"], "status": pay_by[o["order_id"]][0]["status"] if o["order_id"] in pay_by else "none"},
            **({"coupon": o["coupon_code"]} if o["coupon_code"] else {}),
            "total": o["total_amount"], "status_history": hist,
        })
    reviews = [{"_id": r["review_id"], "product_id": r["product_id"], "customer_id": r["customer_id"], "rating": r["rating"],
                "title": r["title"], "verified": r["verified_purchase"], "created_at": ejson_date(r["created_at"])} for r in shop["reviews"]]
    return {"customers": customers, "products": products, "orders": orders, "reviews": reviews}


# --------------------------------------------------------------------------- redis
def q(s: str) -> str:
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def redis_seed(rng: random.Random, shop: dict, analytics: dict) -> str:
    L = ["# Query Lab dataset for Redis, generated by tools/gen_query_lab_data.py (do not edit by hand).",
         "# Load into the lab Redis:  grep -v '^#' NoSQL/lab/datasets/redis/seed.redis | redis-cli -p 6390   (redis-cli has no comment syntax)",
         "# Keys follow the shop and analytics SQL datasets, so the same ids mean the same things.", "FLUSHDB", ""]
    prods = sorted(shop["products"], key=lambda p: p["product_id"])
    L.append("# --- product cache: one hash per product (cache-aside pattern)")
    for p in prods[:80]:
        L.append(f"HSET product:{p['product_id']} name {q(p['name'])} brand {q(p['brand'])} category {q(p['category'])} price {p['price']:.2f} stock {p['stock']}")
    L.append("EXPIRE product:101 3600")
    L.append("EXPIRE product:102 3600")
    L.append("")
    L.append("# --- customer profiles")
    for c in shop["customers"][:60]:
        L.append(f"HSET customer:{c['customer_id']} name {q(c['first_name'] + ' ' + c['last_name'])} email {q(c['email'])} city {q(c['city'])} segment {c['segment']}")
    L.append("")
    sold = {}
    for it in shop["items"]:
        sold[it["product_id"]] = sold.get(it["product_id"], 0) + it["quantity"]
    L.append("# --- best sellers (units sold) and a weekly game leaderboard")
    for pid, n in sorted(sold.items()):
        L.append(f"ZADD bestsellers {n} product:{pid}")
    players = rng.sample([f"{f.lower()}_{rng.randint(10, 99)}" for f in FIRST], 60)
    for pl in players:
        L.append(f"ZADD leaderboard:2025-W40 {rng.randint(120, 9800)} {pl}")
    for pl in rng.sample(players, 40):
        L.append(f"ZADD leaderboard:2025-W41 {rng.randint(120, 9800)} {pl}")
    L.append("")
    L.append("# --- page view counters and per-user rate-limit windows")
    for page, n in [("home", 184213), ("pricing", 40211), ("docs", 77120), ("checkout", 12890)]:
        L.append(f"SET pageviews:{page} {n}")
    for uid in range(1, 9):
        L.append(f"SET ratelimit:user:{uid}:2025-10-05T10:15 {rng.randint(1, 120)} EX 60")
    L.append("")
    L.append("# --- sessions with TTLs (login tokens)")
    for uid in range(1, 16):
        tok = "".join(rng.choice("abcdef0123456789") for _ in range(16))
        L.append(f"SET session:{tok} user:{uid} EX {rng.choice([300, 900, 1800, 3600, 86400])}")
    L.append("")
    L.append("# --- recently viewed products (capped lists) and shopping carts (hashes)")
    for uid in range(1, 21):
        viewed = rng.sample([p["product_id"] for p in prods], 8)
        L.append(f"LPUSH recent:customer:{uid} " + " ".join(f"product:{v}" for v in viewed))
        L.append(f"LTRIM recent:customer:{uid} 0 4")
    for uid in range(1, 13):
        cart = rng.sample([p["product_id"] for p in prods], rng.randint(1, 4))
        L.append(f"HSET cart:customer:{uid} " + " ".join(f"product:{p} {rng.randint(1, 3)}" for p in cart))
    L.append("")
    L.append("# --- a social graph (sets): who follows whom")
    for uid in range(1, 31):
        follows = rng.sample(range(1, 31), rng.randint(3, 10))
        follows = [f for f in follows if f != uid]
        L.append(f"SADD following:{uid} " + " ".join(str(f) for f in follows))
    L.append("")
    L.append("# --- tags per product and products per tag")
    for p in prods[:60]:
        tags = sorted({p["top"].lower().replace(" & ", "-").replace(" ", "-"), p["brand"].lower(), p["category"].lower().replace(" & ", "-").replace(" ", "-")})
        L.append(f"SADD tags:product:{p['product_id']} " + " ".join(tags))
        for t in tags:
            L.append(f"SADD products:tag:{t} {p['product_id']}")
    L.append("")
    L.append("# --- daily active users as bitmaps (bit = user_id) and unique visitors as HyperLogLog")
    days = {}
    for e in analytics["events"]:
        if e[2] == "login" and e[3] >= datetime(2025, 9, 1, tzinfo=timezone.utc) and e[3] < datetime(2025, 9, 8, tzinfo=timezone.utc):
            days.setdefault(e[3].date().isoformat(), set()).add(e[1])
    for d_, ids in sorted(days.items()):
        for uid in sorted(ids):
            L.append(f"SETBIT dau:{d_} {uid} 1")
        L.append(f"PFADD uniques:{d_} " + " ".join(f"u{u}" for u in sorted(ids)))
    L.append("")
    L.append("# --- store locations (geo), real coordinates")
    for c in CITIES:
        L.append(f"GEOADD stores {c[3]} {c[4]} {q(c[0])}")
    L.append("")
    L.append("# --- an order event stream (event sourcing / queues)")
    last = (0, -1)
    for o in sorted(shop["orders"][-40:], key=lambda o: (o["ordered_at"], o["order_id"])):
        ms = int(o["ordered_at"].timestamp() * 1000)
        last = (ms, last[1] + 1) if ms == last[0] else (ms, 0)   # same millisecond: next sequence number
        L.append(f"XADD stream:orders {ms}-{last[1]} order_id {o['order_id']} customer_id {o['customer_id']} status {o['status']} total {o['total_amount']:.2f}")
    L.append("")
    L.append("# --- feature flags and config")
    L.append("HSET config:features new_checkout on dark_mode on recommendations_v2 off")
    L.append("SET config:maintenance_mode off")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- main
def main() -> None:
    rng = random.Random(SEED)
    shop = gen_shop(random.Random(rng.random()))
    hr = gen_hr(random.Random(rng.random()))
    analytics = gen_analytics(random.Random(rng.random()))
    SQL_OUT.mkdir(parents=True, exist_ok=True)
    (SQL_OUT / "shop.sql").write_text(shop_sql(shop))
    (SQL_OUT / "hr.sql").write_text(hr_sql(hr))
    (SQL_OUT / "analytics.sql").write_text(analytics_sql(analytics))
    mdir = NOSQL_OUT / "mongodb"
    mdir.mkdir(parents=True, exist_ok=True)
    for name, docs in mongo_docs(shop).items():
        (mdir / f"{name}.json").write_text("[\n" + ",\n".join(json.dumps(d, separators=(",", ":")) for d in docs) + "\n]\n")
    rdir = NOSQL_OUT / "redis"
    rdir.mkdir(parents=True, exist_ok=True)
    (rdir / "seed.redis").write_text(redis_seed(random.Random(rng.random()), shop, analytics))
    print(f"shop: {len(shop['customers'])} customers, {len(shop['products'])} products, {len(shop['orders'])} orders, "
          f"{len(shop['items'])} items, {len(shop['payments'])} payments, {len(shop['reviews'])} reviews")
    print(f"hr: {len(hr['employees'])} employees, {len(hr['salary_history'])} salary rows, {len(hr['projects'])} projects, "
          f"{len(hr['employee_projects'])} assignments, {len(hr['applications'])} applications")
    print(f"analytics: {len(analytics['users'])} users, {len(analytics['events'])} events, "
          f"{len(analytics['subscriptions'])} subscriptions, {len(analytics['experiment'])} experiment rows")
    for f in sorted([*SQL_OUT.glob("*.sql"), *mdir.glob("*.json"), rdir / "seed.redis"]):
        print(f"  {f.relative_to(ROOT)}  {f.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()

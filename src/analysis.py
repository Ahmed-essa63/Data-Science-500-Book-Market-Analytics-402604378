
import csv
import os
import json
import math
import html
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "books_raw.csv")
OUT = os.path.join(ROOT, "data", "processed")
FIG = os.path.join(ROOT, "reports", "figures")

os.makedirs(OUT, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

def number(value):
    try:
        return float(str(value).replace("£", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return None

def rating_number(value):
    text = str(value).strip().lower()
    words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
    for word, score in words.items():
        if word in text:
            return score
    n = number(text)
    if n is not None and 1 <= n <= 5:
        return n
    return None

with open(RAW, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    original_fields = reader.fieldnames or []

if not rows:
    raise SystemExit("No books found in the raw CSV.")

def get_value(row, candidates):
    for key in row:
        if key and key.strip().lower().replace(" ", "_") in candidates:
            return row[key]
    return ""

clean = []
for row in rows:
    title = get_value(row, {"title", "book_title", "name"})
    price = number(get_value(row, {"price_gbp", "price", "price_£", "price_gbp_"}))
    rating = rating_number(get_value(row, {"rating", "star_rating", "stars"}))
    availability = get_value(row, {"availability", "stock", "stock_availability"})
    quantity = get_value(row, {"quantity", "stock_quantity", "availability_quantity"})
    url = get_value(row, {"url", "product_url", "link"})

    if price is None:
        for key, value in row.items():
            if key and "price" in key.lower():
                price = number(value)
                if price is not None:
                    break

    if not title:
        title = get_value(row, {original_fields[0].strip().lower().replace(" ", "_")}) if original_fields else ""

    if not title or price is None:
        continue

    clean.append({
        "title": title.strip(),
        "price_gbp": round(price, 2),
        "rating": rating if rating is not None else "",
        "availability": availability.strip(),
        "quantity": quantity.strip(),
        "url": url.strip()
    })

if not clean:
    print("CSV columns found:", original_fields)
    raise SystemExit("Could not identify book titles and prices. Send me the CSV header row.")

clean_file = os.path.join(OUT, "books_clean.csv")
fields = ["title", "price_gbp", "rating", "availability", "quantity", "url"]
with open(clean_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(clean)

prices = [r["price_gbp"] for r in clean]
rated = [r for r in clean if r["rating"] != ""]
ratings = [r["rating"] for r in rated]

mean_price = sum(prices) / len(prices)
sorted_prices = sorted(prices)
median_price = sorted_prices[len(sorted_prices) // 2]
min_price = min(prices)
max_price = max(prices)

# Simple linear regression: predict price using star rating.
# Calculated with ordinary Python arithmetic.
x = [float(r["rating"]) for r in rated]
y = [float(r["price_gbp"]) for r in rated]
model = {"method": "Simple linear regression", "feature": "rating", "target": "price_gbp"}

if len(x) >= 2 and len(set(x)) > 1:
    xbar = sum(x) / len(x)
    ybar = sum(y) / len(y)
    denom = sum((v - xbar) ** 2 for v in x)
    slope = sum((x[i] - xbar) * (y[i] - ybar) for i in range(len(x))) / denom
    intercept = ybar - slope * xbar
    predictions = [intercept + slope * v for v in x]
    ss_res = sum((y[i] - predictions[i]) ** 2 for i in range(len(y)))
    ss_tot = sum((v - ybar) ** 2 for v in y)
    r2 = 1 - ss_res / ss_tot if ss_tot else 0
    model.update({
        "slope": round(slope, 4),
        "intercept": round(intercept, 4),
        "r_squared": round(r2, 4),
        "rated_books_used": len(x),
        "example_prediction_rating_3": round(intercept + slope * 3, 2)
    })
else:
    model["note"] = "Not enough different rating values to fit regression."

with open(os.path.join(ROOT, "reports", "model_metrics.json"), "w", encoding="utf-8") as f:
    json.dump(model, f, indent=2)

# Create an SVG price chart using only the standard library.
bins = Counter()
for price in prices:
    low = int(price // 5) * 5
    bins[low] += 1

max_count = max(bins.values()) or 1
bar_width = 500 / max(1, len(bins))
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="760" height="450">',
       '<rect width="100%" height="100%" fill="white"/>',
       '<text x="380" y="28" text-anchor="middle" font-size="20">Book Price Distribution</text>',
       '<text x="380" y="435" text-anchor="middle" font-size="14">Price range (GBP)</text>',
       '<text x="20" y="220" transform="rotate(-90 20 220)" text-anchor="middle" font-size="14">Number of books</text>']
for i, (low, count) in enumerate(sorted(bins.items())):
    x_pos = 100 + i * bar_width
    height = 330 * count / max_count
    y_pos = 390 - height
    svg.append(f'<rect x="{x_pos:.1f}" y="{y_pos:.1f}" width="{max(2, bar_width-2):.1f}" height="{height:.1f}" fill="#4776a8"/>')
    svg.append(f'<text x="{x_pos + bar_width/2:.1f}" y="408" text-anchor="middle" font-size="9">{low}</text>')
svg.append("</svg>")
with open(os.path.join(FIG, "price_distribution.svg"), "w", encoding="utf-8") as f:
    f.write("\n".join(svg))

rating_counts = Counter(str(r["rating"]) for r in rated)
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400">',
       '<rect width="100%" height="100%" fill="white"/>',
       '<text x="300" y="30" text-anchor="middle" font-size="20">Books by Star Rating</text>']
for i, score in enumerate(sorted(rating_counts)):
    count = rating_counts[score]
    y_pos = 70 + i * 60
    width = 400 * count / (max(rating_counts.values()) or 1)
    svg.append(f'<text x="35" y="{y_pos+22}" font-size="14">{html.escape(score)} stars</text>')
    svg.append(f'<rect x="120" y="{y_pos}" width="{width:.1f}" height="32" fill="#4b9b78"/>')
    svg.append(f'<text x="{130+width:.1f}" y="{y_pos+22}" font-size="13">{count}</text>')
svg.append("</svg>")
with open(os.path.join(FIG, "rating_distribution.svg"), "w", encoding="utf-8") as f:
    f.write("\n".join(svg))

availability_counts = Counter(
    r["availability"] or "Not recorded" for r in clean
)

report = f"""# Book Market Analytics Report

## 1. Introduction
This project collects and analyses book listing data from Books to Scrape. The objective is to explore prices, ratings and availability and demonstrate a basic regression model.

## 2. Data collection
The raw dataset contains {len(rows)} scraped listings. The cleaned dataset contains {len(clean)} records with identifiable titles and prices. The fields include title, price in GBP, star rating, availability, quantity where provided, and product URL where available.

## 3. Data cleaning
The analysis removes records without a usable title or price, converts prices to numeric GBP values, converts recognised star ratings to numbers from 1 to 5, and saves the result to data/processed/books_clean.csv. Missing ratings are left blank rather than invented.

## 4. Descriptive analysis
- Books retained after cleaning: {len(clean)}
- Average price: £{mean_price:.2f}
- Median price: £{median_price:.2f}
- Minimum price: £{min_price:.2f}
- Maximum price: £{max_price:.2f}
- Books with recognised ratings: {len(rated)}

Price distribution chart: reports/figures/price_distribution.svg

Rating distribution chart: reports/figures/rating_distribution.svg

## 5. Linear regression
A simple ordinary least-squares linear regression uses star rating as the predictor and price in GBP as the target. Model results are saved in reports/model_metrics.json.

{json.dumps(model, indent=2)}

This is an exploratory model, not evidence that a higher rating causes a higher price. Ratings alone may not explain price differences, and the model should not be used as a reliable pricing tool without further validation.

## 6. Conclusion
The collected listings provide a basic view of book prices, ratings and availability. The cleaned CSV and charts support further analysis. Future work could add book categories, compare prices between categories, and evaluate predictive accuracy on a separate test set.

## 7. References
Books to Scrape (n.d.) *Books to Scrape*. Available at: https://books.toscrape.com/ (Accessed: 23 October 2026).

Python Software Foundation (n.d.) *Python 3 Documentation*. Available at: https://docs.python.org/3/ (Accessed: 23 October 2026).
"""
with open(os.path.join(ROOT, "reports", "project_report.md"), "w", encoding="utf-8") as f:
    f.write(report)

print("ANALYSIS COMPLETE")
print("Raw listings:", len(rows))
print("Cleaned listings:", len(clean))
print(f"Average price: £{mean_price:.2f}")
print("Clean dataset:", clean_file)
print("Report: reports/project_report.md")
print("Charts: reports/figures/")
print("Regression metrics: reports/model_metrics.json")

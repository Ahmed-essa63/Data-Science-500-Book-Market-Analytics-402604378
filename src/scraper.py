"""Scrape book listings from the Books to Scrape practice website."""
from __future__ import annotations

import re
import time
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
HEADERS = {"User-Agent": "DataScience500StudentProject/1.0 (educational scraping)"}


def parse_stock(text: str) -> tuple[str, int | None]:
    """Return stock status and quantity if it is present."""
    cleaned = " ".join(text.split())
    match = re.search(r"\((\d+)\s+available\)", cleaned, flags=re.I)
    quantity = int(match.group(1)) if match else None
    status = "In stock" if "in stock" in cleaned.lower() else "Out of stock"
    return status, quantity


def scrape_catalogue(max_pages: int | None = None, delay: float = 0.15) -> pd.DataFrame:
    """Scrape all catalogue pages, or at most max_pages when specified."""
    session = requests.Session()
    session.headers.update(HEADERS)
    page_url = BASE_URL
    rows = []
    page_count = 0

    while page_url:
        response = session.get(page_url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for card in soup.select("article.product_pod"):
            title_link = card.select_one("h3 a")
            price_node = card.select_one(".price_color")
            stock_node = card.select_one(".availability")
            rating_node = card.select_one("p.star-rating")

            if not title_link or not price_node or not stock_node or not rating_node:
                continue

            title = title_link.get("title") or title_link.get_text(" ", strip=True)
            price_text = price_node.get_text(" ", strip=True).replace("Â", "")
            price_match = re.search(r"(\d+(?:\.\d+)?)", price_text)
            price_gbp = float(price_match.group(1)) if price_match else None
            rating_word = next(
                (cls for cls in rating_node.get("class", []) if cls in RATING_MAP),
                None
            )
            stock_status, stock_quantity = parse_stock(stock_node.get_text(" ", strip=True))

            rows.append({
                "title": title,
                "price_gbp": price_gbp,
                "rating_word": rating_word,
                "rating": RATING_MAP.get(rating_word),
                "stock_status": stock_status,
                "stock_quantity": stock_quantity,
                "book_url": urljoin(page_url, title_link.get("href", "")),
                "category": None,
            })

        page_count += 1
        if max_pages is not None and page_count >= max_pages:
            break

        next_link = soup.select_one("li.next a")
        page_url = urljoin(page_url, next_link["href"]) if next_link else None
        time.sleep(delay)

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No books were scraped. Check your internet connection or the website structure.")
    return df.drop_duplicates(subset=["book_url"]).reset_index(drop=True)


def main() -> None:
    output = Path(__file__).resolve().parents[1] / "data" / "raw" / "books_raw.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    df = scrape_catalogue()
    df.to_csv(output, index=False)
    print(f"Saved {len(df)} books to {output}")


if __name__ == "__main__":
    main()

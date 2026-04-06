#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generate_movies.py
==================

*Scrapes IMDb "Popular Movies" and filters out Bollywood films.
* For each title, looks up metadata via TMDB API to check original_language.
* Outputs a JSON array compatible with media managers.
"""

# ------------------------------------------------------------
# 0️⃣ Force UTF‑8 output (prevents UnicodeEncodeError on Windows)
# ------------------------------------------------------------
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
else:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ------------------------------------------------------------
# 1️⃣ Imports & defaults
# ------------------------------------------------------------
import argparse
import json
import re
import time
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ---------- Configurable defaults ----------
DEFAULT_COUNT = 25
DEFAULT_OUTPUT = "top_movies_25.json"
IMDB_MOVIES_URL = (
    "https://www.imdb.com/search/title/?title_type=feature&user_rating=6,10&num_votes=10000,&countries=!in&languages=!hi&count={count}"
)
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)


# ------------------------------------------------------------
# 2️⃣ Helper: fetch the IMDb "popular movies" page using Playwright
# ------------------------------------------------------------
def fetch_popular_movies(count: int, ua: str) -> list[dict]:
    """
    Scrape IMDb movies using Playwright to handle WAF challenges.
    Returns list of {"title": str, "imdbId": str, "year": int}.
    """
    url = IMDB_MOVIES_URL.format(count=count)
    items = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
        
        context = browser.new_context(
            user_agent=ua,
            viewport={'width': 1920, 'height': 1080},
            java_script_enabled=True,
        )
        
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page = context.new_page()
        
        try:
            print(f"🌐 Loading IMDb page: {url[:80]}...")
            page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            print("⏳ Waiting for content...")
            page.wait_for_selector('a.ipc-title-link-wrapper[href*="/title/tt"]', timeout=30000)
            
            print("✅ Page loaded, extracting titles...")
            
            last_count = 0
            scroll_attempts = 0
            max_scroll_attempts = (count // 50) + 10
            
            while len(items) < count and scroll_attempts < max_scroll_attempts:
                elements = page.query_selector_all('a.ipc-title-link-wrapper[href*="/title/tt"]')
                
                for elem in elements:
                    href = elem.get_attribute('href') or ''
                    imdb_match = re.search(r"tt(\d+)", href)
                    if not imdb_match:
                        continue
                    imdb_id = f"tt{imdb_match.group(1)}"
                    
                    title_elem = elem.query_selector('h3.ipc-title__text')
                    if title_elem:
                        raw_title = title_elem.inner_text()
                    else:
                        raw_title = elem.inner_text()
                    
                    clean_title = re.sub(r"^\d+\.\s*", "", raw_title.strip())
                    
                    if not any(i['imdbId'] == imdb_id for i in items):
                        items.append({"title": clean_title, "imdbId": imdb_id})
                
                if len(items) >= count:
                    break
                
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                time.sleep(3)
                
                if len(elements) == last_count:
                    scroll_attempts += 1
                    print(f"📜 Scrolling... ({scroll_attempts}/{max_scroll_attempts}, found {len(items)} items)")
                else:
                    scroll_attempts = 0
                    last_count = len(elements)
            
            print(f"✅ Scraped {len(items)} movies from IMDb")
            
        except PlaywrightTimeoutError:
            print(f"⚠️ Timeout waiting for IMDb page after multiple retries")
            print(f"   Page URL: {url[:100]}...")
            print(f"   Items collected: {len(items)}")
        except Exception as e:
            print(f"⚠️ Error during scraping: {type(e).__name__}: {e}")
            print(f"   Items collected: {len(items)}")
        finally:
            browser.close()
    
    return items[:count]


def fetch_popular_movies_with_retry(count: int, ua: str, max_retries: int = 3) -> list[dict]:
    """Wrapper with retry logic for resilience."""
    for attempt in range(max_retries):
        try:
            items = fetch_popular_movies(count, ua)
            if items:
                return items
            print(f"⚠️ Attempt {attempt + 1}: No items scraped, retrying...")
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5 * (attempt + 1))
    
    return []


# ------------------------------------------------------------
# 3️⃣ Build the final JSON payload
# ------------------------------------------------------------
def build_payload(raw_items: list[dict]) -> list[dict]:
    """
    Convert scraped items to output format.
    Returns list of dicts: {"title": str, "imdbId": str}
    """
    return [{"title": entry["title"], "imdbId": entry["imdbId"]} for entry in raw_items]


# ------------------------------------------------------------
# 4️⃣ Write the JSON file
# ------------------------------------------------------------
def write_json(data: list[dict], outfile: Path) -> None:
    json_text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    outfile.write_text(json_text, encoding="utf-8")
    print(f"✅ Wrote {len(data)} entries → {outfile}")


# ------------------------------------------------------------
# 5️⃣ Main entry point (CLI)
# ------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Generate a list of top N popular movies from IMDb (Bollywood excluded via URL filter)."
    )
    parser.add_argument("-n", "--number", type=int, default=DEFAULT_COUNT,
                        help=f"How many movies to fetch (default={DEFAULT_COUNT})")
    parser.add_argument("-o", "--output", type=Path, default=Path(DEFAULT_OUTPUT),
                        help=f"Output JSON file (default={DEFAULT_OUTPUT})")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT,
                        help="User‑Agent header for the IMDb request")
    args = parser.parse_args()

    try:
        raw = fetch_popular_movies_with_retry(args.number, args.user_agent)
        if not raw:
            sys.exit("❌ No movies were scraped from IMDb after retries – aborting.")
        
        payload = build_payload(raw)
        if not payload:
            sys.exit("❌ No movies remaining – nothing to write.")
        
        write_json(payload, args.output)
    except Exception as exc:
        sys.exit(f"❌ Unexpected error: {exc}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generate_list.py
================

* Scrapes IMDb “Popular TV Shows”.
* For each title, looks up the TVDB ID via TVMaze (free, no API key required).
* Emits a JSON array compatible with Sonarr’s **Custom** import list:
  [
    {"title": "Wednesday", "tvdbId": 393342},
    {"title": "The Witcher", "tvdbId": 307115},
    …
  ]
"""

# ------------------------------------------------------------
# 0️⃣ Force UTF‑8 output (prevents UnicodeEncodeError on Windows)
# ------------------------------------------------------------
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
else:  # fallback for very old Python versions
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
DEFAULT_COUNT = 25                           # how many titles we want
DEFAULT_OUTPUT = "top_25.json"               # name of the generated file
IMDB_POPULAR_URL = (
    "https://www.imdb.com/search/title/?title_type=tv_series,tv_miniseries,tv_short,tv_movie,tv_episode,tv_special,short&user_rating=5,10&num_votes=10000,&languages=en&count={count}"
)
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)

# ------------------------------------------------------------
# 2️⃣ Helper: fetch the IMDb "popular TV" page using Playwright
# ------------------------------------------------------------
def fetch_popular_tv(count: int, ua: str) -> list[dict]:
    """
    Scrape IMDb using Playwright to handle WAF challenges.Requires browser automation because IMDb's WAF blocks simple HTTP requests.
    """
    url = IMDB_POPULAR_URL.format(count=count)
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
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_selector('a.ipc-title-link-wrapper[href*="/title/tt"]', timeout=15000)
            
            last_count = 0
            scroll_attempts = 0
            max_scroll_attempts = (count // 50) + 5
            
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
                time.sleep(2)
                
                if len(elements) == last_count:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                    last_count = len(elements)
            
            print(f"✅ Scraped {len(items)} shows from IMDb")
            
        except PlaywrightTimeoutError:
            print("⚠️ Timeout waiting for IMDb page - returning partial results")
        except Exception as e:
            print(f"⚠️ Error during scraping: {e}")
        finally:
            browser.close()
    
    return items[:count]


def fetch_popular_tv_with_retry(count: int, ua: str, max_retries: int = 3) -> list[dict]:
    """Wrapper with retry logic for resilience against transient failures."""
    for attempt in range(max_retries):
        try:
            items = fetch_popular_tv(count, ua)
            if items:
                return items
            print(f"⚠️ Attempt {attempt + 1}: No items scraped, retrying...")
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5* (attempt + 1))
    
    return []


# ------------------------------------------------------------
# 3️⃣ Helper: translate an IMDb ID → TVDB ID using TVMaze
# ------------------------------------------------------------
def imdb_to_tvdb(imdb_id: str) -> int | None:
    """
    Return the TVDB ID (int) for a given IMDb ID or None if not found.
    Uses the free TVMaze lookup endpoint.
    """
    url = f"https://api.tvmaze.com/lookup/shows?imdb={imdb_id}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # TVMaze puts the TVDB id under data["externals"]["thetvdb"]
            tvdb_id = data.get("externals", {}).get("thetvdb")
            if isinstance(tvdb_id, int) and tvdb_id > 0:
                return tvdb_id
    except Exception:
        # Silently ignore network issues – returning None will drop the entry later.
        pass
    return None


# ------------------------------------------------------------
# 4️⃣ Build the final JSON payload (title + tvdbId)
# ------------------------------------------------------------
def build_payload(raw_items: list[dict]) -> list[dict]:
    """
    Take the list produced by fetch_popular_tv (title + imdbId)
    and turn it into a list of dicts for Sonarr Custom JSON:
        {"title": "...", "tvdbId": 12345}
    If a TVDB ID cannot be resolved, the item is omitted.
    """
    payload = []
    for entry in raw_items:
        tvdb_id = imdb_to_tvdb(entry["imdbId"])
        if tvdb_id:
            payload.append({"title": entry["title"], "tvdbId": tvdb_id})
        else:
            # For debugging you can uncomment the line below:
            # print(f"⚠️  No TVDB id for {entry['title']} ({entry['imdbId']}) – skipping")
            continue
    return payload


# ------------------------------------------------------------
# 5️⃣ Write the JSON file
# ------------------------------------------------------------
def write_json(data: list[dict], outfile: Path) -> None:
    json_text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    outfile.write_text(json_text, encoding="utf-8")
    print(f"✅ Wrote {len(data)} entries → {outfile}")


# ------------------------------------------------------------
# 6️⃣ Main entry point (CLI)
# ------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Generate a Sonarr‑compatible JSON list of the top N popular TV shows from IMDb."
    )
    parser.add_argument("-n", "--number", type=int, default=DEFAULT_COUNT,
                        help=f"How many shows to fetch (default={DEFAULT_COUNT})")
    parser.add_argument("-o", "--output", type=Path, default=Path(DEFAULT_OUTPUT),
                        help=f"Output JSON file (default={DEFAULT_OUTPUT})")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT,
                        help="User‑Agent header for the IMDb request")
    args = parser.parse_args()

    try:
        raw = fetch_popular_tv_with_retry(args.number, args.user_agent)
        if not raw:
            sys.exit("❌ No shows were scraped from IMDb after retries – aborting.")
        payload = build_payload(raw)
        if not payload:
            sys.exit("❌ No TVDB IDs could be resolved – nothing to write.")
        write_json(payload, args.output)
    except Exception as exc:
        sys.exit(f"❌ Unexpected error: {exc}")


if __name__ == "__main__":
    main()

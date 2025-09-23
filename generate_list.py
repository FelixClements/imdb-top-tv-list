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
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---------- Configurable defaults ----------
DEFAULT_COUNT = 25                           # how many titles we want
DEFAULT_OUTPUT = "top_25.json"               # name of the generated file
IMDB_POPULAR_URL = (
    "https://www.imdb.com/search/title/?title_type=tv_series,tv_miniseries,tv_short,tv_movie,tv_episode&languages=en&count={count}"
)
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; imdb-tv-list/1.0; +https://github.com/youruser/imdb-top-tv-list)"
)

# ------------------------------------------------------------
# 2️⃣ Helper: fetch the IMDb “popular TV” page
# ------------------------------------------------------------
def fetch_popular_tv(count: int, ua: str) -> list[dict]:
    url = IMDB_POPULAR_URL.format(count=count)
    resp = requests.get(url, headers={"User-Agent": ua}, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    items = []

    # New IMDb layout: <a class="ipc-title-link-wrapper" href="/title/tt1234567/…">
    for a_tag in soup.select('a.ipc-title-link-wrapper[href*="/title/tt"]'):
        href = a_tag["href"]
        imdb_match = re.search(r"tt(\d+)", href)
        if not imdb_match:
            continue
        imdb_id = f"tt{imdb_match.group(1)}"

        # Title is inside a <h3 class="ipc-title__text …">
        title_tag = a_tag.select_one("h3.ipc-title__text")
        if not title_tag:
            # Safety fallback – use the <a> text itself.
            raw_title = a_tag.get_text(strip=True)
        else:
            raw_title = title_tag.get_text(strip=True)

        # Strip the leading rank number (“1. Wednesday” → “Wednesday”)
        clean_title = re.sub(r"^\d+\.\s*", "", raw_title)

        items.append({"title": clean_title, "imdbId": imdb_id})

        if len(items) >= count:
            break

    # --------------------------------------------------------
    # Fallback for any future IMDb redesign – keep the old logic.
    # --------------------------------------------------------
    if not items:
        for entry in soup.select("div.lister-item"):
            header = entry.select_one("h3.lister-item-header")
            if not header:
                continue
            a = header.select_one("a")
            if not a:
                continue
            title = a.get_text(strip=True)
            m = re.search(r"/title/(tt\d+)/", a["href"])
            if not m:
                continue
            imdb_id = m.group(1)
            items.append({"title": title, "imdbId": imdb_id})
            if len(items) >= count:
                break

    return items


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
        raw = fetch_popular_tv(args.number, args.user_agent)
        if not raw:
            sys.exit("❌ No shows were scraped from IMDb – aborting.")
        payload = build_payload(raw)
        if not payload:
            sys.exit("❌ No TVDB IDs could be resolved – nothing to write.")
        write_json(payload, args.output)
    except Exception as exc:
        sys.exit(f"❌ Unexpected error: {exc}")


if __name__ == "__main__":
    main()

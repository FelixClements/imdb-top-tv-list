#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generate_list.py
================

Creates a JSON file containing the top‑N popular TV series from IMDb.
The script now works with the *new* IMDb HTML layout (as of 2024‑2025).

The output file can be fed straight to Sonarr through its
“Import Lists → Custom JSON” feature.
"""

# ------------------------------------------------------------
# 0️⃣ Make sure stdout / stderr are UTF‑8 (prevents
#     UnicodeEncodeError on Windows / old terminals)
# ------------------------------------------------------------
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
else:  # pragma: no cover – Python < 3.7 fallback
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ------------------------------------------------------------
# 1️⃣ Imports & constants
# ------------------------------------------------------------
import argparse
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ----------------------------------------------------------------------
# USER‑CONFIGURABLE defaults (override on the CLI if you wish)
# ----------------------------------------------------------------------
DEFAULT_COUNT = 25                     # how many titles to fetch
DEFAULT_OUTPUT = "top_25.json"         # output file name
IMDB_POPULAR_URL = (
    "https://www.imdb.com/search/title/?title_type=tv_series&count={count}"
)
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; imdb-tv-list/1.0; +https://github.com/youruser/imdb-top-tv-list)"
)

# ----------------------------------------------------------------------
def fetch_popular_tv(count: int, ua: str) -> list[dict]:
    """
    Scrape the *current* IMDb “Popular TV Shows” page and return a list like:
        [{"title": "...", "imdbId": "tt1234567"}, …]

    Parameters
    ----------
    count : int
        Number of series to return (IMDb returns up to 100 per page, so we just cut
        the list after we have `count` items).
    ua : str
        User‑Agent header – required because IMDb blocks default python‑requests
        agents.
    """
    url = IMDB_POPULAR_URL.format(count=count)
    headers = {"User-Agent": ua}
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    # ------------------------------------------------------------
    # New IMDb layout:  <a class="ipc-title-link-wrapper" href="/title/tt...">
    # ------------------------------------------------------------
    for a_tag in soup.select('a.ipc-title-link-wrapper[href*="/title/tt"]'):
        href = a_tag.get("href", "")
        # Extract the IMDb‑ID (tt1234567) from the href.
        imdb_match = re.search(r"tt\d+", href)
        if not imdb_match:
            continue
        imdb_id = imdb_match.group(0)

        # The title lives in a nested <h3 class="ipc-title__text ...">
        title_tag = a_tag.select_one("h3.ipc-title__text")
        if not title_tag:
            # As a super‑fallback, use the text of the <a> itself.
            raw_title = a_tag.get_text(separator=" ", strip=True)
        else:
            raw_title = title_tag.get_text(strip=True)

        # IMDb prefixes the title with a ranking number (e.g. "1. Wednesday").
        # Strip that leading "1. ", "2. " etc.
        clean_title = re.sub(r"^\d+\.\s*", "", raw_title)

        results.append({"title": clean_title, "imdbId": imdb_id})

        if len(results) >= count:
            break

    # Safety net – if the new selector did not find anything (maybe IMDb changed
    # again), we fall back to the *old* selector used before 2024.
    if not results:
        # --- old style (left for compatibility) --------------------------------
        old_items = soup.select("div.lister-item")
        for entry in old_items:
            header = entry.select_one("h3.lister-item-header")
            if not header:
                continue
            a = header.select_one("a")
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a["href"]
            imdb_match = re.search(r"/title/(tt\d+)/", href)
            if not imdb_match:
                continue
            imdb_id = imdb_match.group(1)
            results.append({"title": title, "imdbId": imdb_id})
            if len(results) >= count:
                break

    return results


# ----------------------------------------------------------------------
def write_json(data: list[dict], outfile: Path) -> None:
    """Write *data* to *outfile* as pretty‑printed UTF‑8 JSON."""
    json_text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    outfile.write_text(json_text, encoding="utf-8")
    # The print now uses the UTF‑8 stdout set at the top of the file.
    print(f"✅ Wrote {len(data)} entries → {outfile}")


# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate a JSON file containing the top N popular TV shows from IMDb. "
            "The output can be used directly by Sonarr's Import Lists → Custom JSON."
        )
    )
    parser.add_argument(
        "-n",
        "--number",
        type=int,
        default=DEFAULT_COUNT,
        help=f"How many shows to fetch (default: {DEFAULT_COUNT})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(DEFAULT_OUTPUT),
        help=f"Output JSON filename (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--user-agent",
        default=DEFAULT_USER_AGENT,
        help="Custom User‑Agent header for the IMDb request",
    )
    args = parser.parse_args()

    try:
        shows = fetch_popular_tv(args.number, args.user_agent)
        if not shows:
            sys.exit("❌ No TV shows were extracted – aborting.")
        write_json(shows, args.output)
    except Exception as exc:
        # Any unexpected exception is printed using UTF‑8‑safe output.
        sys.exit(f"❌ Unexpected error: {exc}")


# ----------------------------------------------------------------------
if __name__ == "__main__":
    main()
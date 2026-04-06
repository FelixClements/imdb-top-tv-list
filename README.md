# 🎬 IMDb Top Lists → Sonarr & Radarr

**Automated daily generation of popular IMDb TV shows (Sonarr) and movies (Radarr) as JSON import lists.**

[![GitHub Actions](https://github.com/FelixClements/imdb-top-lists/workflows/Update%20IMDb%20Lists/badge.svg)](https://github.com/FelixClements/imdb-top-lists/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ What This Does

This repository automatically generates and updates JSON lists of popular content from IMDb:

| Content Type | Output Files | Use With |
|--------------|--------------|----------|
| 📺 **TV Shows** | `top_tvshows_5.json`, `top_tvshows_10.json`, `top_tvshows_25.json` | **Sonarr** |
| 🎥 **Movies** | `top_movies_5.json`, `top_movies_10.json`, `top_movies_25.json` | **Radarr** |

**Key Features:**
- 🔄 **Daily automation** - GitHub Actions updates lists every day at 03:00 UTC
- 🎬 **Bollywood excluded** - Movies list automatically filters Indian cinema
- 🔍 **TVDB resolution** - TV shows include TVDB IDs for Sonarr compatibility
- 🚀 **Playwright-powered** - Bypasses IMDb's anti-bot protection
- 📦 **Zero maintenance** - Works automatically once set up

---

## 📋 Output Format

### TV Shows (Sonarr)
```json
[
  {"title": "One Piece", "tvdbId": 392276},
  {"title": "The Pitt", "tvdbId": 448176},
  {"title": "Invincible", "tvdbId": 368207}
]
```

### Movies (Radarr)
```json
[
  {"title": "Project Hail Mary", "imdbId": "tt12042730"},
  {"title": "The Super Mario Galaxy Movie", "imdbId": "tt28650488"}
]
```

---

## 🚀 Quick Start

### Import to Sonarr

1. Open **Sonarr** → **Settings** → **Import Lists**
2. Click **+** → **Custom**
3. Set:
   - **List Name:** `IMDb Top TV Shows`
   - **List URL:** `https://raw.githubusercontent.com/FelixClements/imdb-top-lists/main/top_tvshows_25.json`
4. Save and enable

### Import to Radarr

1. Open **Radarr** → **Settings** → **Import Lists**
2. Click **+** → **Custom**
3. Set:
   - **List Name:** `IMDb Top Movies`
   - **List URL:** `https://raw.githubusercontent.com/FelixClements/imdb-top-lists/main/top_movies_25.json`
4. Save and enable

---

## 🛠️ Local Usage

### Prerequisites

- Python 3.9+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/FelixClements/imdb-top-lists.git
cd imdb-top-lists

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium --with-deps

# Run the scrapers
python generate_list.py      # TV shows → top_tvshows_25.json
python generate_movies.py   # Movies → top_movies_25.json
```

### Custom Options

```bash
# Generate top 50 TV shows
python generate_list.py -n 50 -o top_tvshows_50.json

# Generate top 100 movies
python generate_movies.py -n 100 -o top_movies_100.json
```

---

## ⚙️ Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `-n, --number` | 25 | Number of titles to fetch |
| `-o, --output` | `top_tvshows_25.json` / `top_movies_25.json` | Output filename |
| `--user-agent` | Chrome 140 | Custom User-Agent header |

---

## 🎬 Bollywood Filtering

Movie list automatically excludes Indian cinema using IMDb URL parameters:
- `countries=!in` - Excludes India as country of origin
- `languages=!hi` - Excludes Hindi language films

This ensures a Western/international focus while respecting that Bollywood content has dedicated platforms.

---

## 🔄 GitHub Actions Workflow

The workflow runs automatically every day at 03:00 UTC:

```yaml
Jobs:
1. Checkout repository
2. Setup Python 3.11
3. Install dependencies
4. Install Playwright browsers
5. Generate TV show lists (5, 10, 25)
6. Generate movie lists (5, 10, 25)
7. Commit changes (if any)
```

**Manual trigger:** Go to **Actions** → **Update IMDb Lists** → **Run workflow**

---

## 📊 How It Works

### Architecture

```
┌─────────────────┐
│  GitHub Actions │
│  (Daily 03:00)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Playwright     │ ◄── Bypasses WAF protection
│  Chromium Browser│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  IMDb Scraper   │ ◄── Scrapes popular TV/movies
└────────┬────────┘
         │
         ├──► TV Shows ──► TVMaze API ──► TVDB ID
         │
         └──► Movies (Bollywood filtered)
         │
         ▼
   JSON Files (committed to repo)
         │
         ▼
   Sonarr / Radarr import
```

---

## 📈 Files Generated

| File | Content | Source |
|------|---------|--------|
| `top_tvshows_5.json` | Top 5 TV shows | IMDb Popular TV |
| `top_tvshows_10.json` | Top 10 TV shows | IMDb Popular TV |
| `top_tvshows_25.json` | Top 25 TV shows | IMDb Popular TV |
| `top_movies_5.json` | Top 5 movies | IMDb Popular Movies |
| `top_movies_10.json` | Top 10 movies | IMDb Popular Movies |
| `top_movies_25.json` | Top 25 movies | IMDb Popular Movies |

---

## 🔧 Troubleshooting

### Playwright Browser Issues

```bash
# Reinstall Playwright browsers
playwright install chromium --with-deps
```

### No Items Scraped

The scraper includes retry logic (3 attempts) and increased timeouts for reliability. If issues persist:
1. Check internet connection
2. Verify IMDb URL is accessible
3. Check GitHub Actions logs for details

---

## 🤝 Contributing

Contributions welcome! Feel free to:
- Report bugs via [Issues](https://github.com/FelixClements/imdb-top-lists/issues)
- Suggest features
- Submit pull requests

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 📜 Changelog

### 2026-04-06
- **Breaking:** Renamed output files to `top_tvshows_X.json` and `top_movies_X.json`
- Added movie scraper for Radarr with Bollywood exclusion
- Fixed WAF blocking by switching to Playwright browser automation
- Improved timeouts for GitHub Actions reliability
- Added detailed logging for debugging

### Historical
- Initial release: TV show scraper for Sonarr
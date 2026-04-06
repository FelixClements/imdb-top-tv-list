# 📺 IMDb-Top-TV-List → Sonarr / Radarr

**Automated nightly generation of JSON files containing the top-N popular TV series and movies on IMDb, enriched with TVDB/IMDb IDs**.  
The files are published via GitHub Actions and can be consumed by:
- **Sonarr** → Settings → Import Lists → Custom (for TV shows)
- **Radarr** → Settings → Import Lists → Custom (for movies)

---

## 🎯 Why this repo?

- **Never miss a hit** – every night the list is refreshed from IMDb's "Popular TV Shows" and "Popular Movies" pages.  
- **Sonarr/Radarr-ready JSON** – TV entries include `title` and `tvdbId`; movie entries include `title` and `imdbId`.
- **Bollywood-filtered movies** – movie list automatically excludes Indian cinema using IMDb URL parameters.
- **Zero-maintenance** – once set up the whole pipeline runs automatically.
- **Fully open source** – MIT licensed, easy to fork or extend.

---

## ✨ Features

| Feature | Details |
|--------|----------|
| ✅ Scrapes the latest IMDb "Popular TV Shows" page | Handles the new IMDb layout (`ipc-title-link-wrapper`). |
| 🎬 Scrapes the latest IMDb "Popular Movies" page | Bollywood films excluded via URL filter (`countries=!in&languages=!hi`). |
| 🔎 TV: Resolves IMDb IDs to TVDB IDs via **TVMaze** (free, no API key) | Guarantees Sonarr can add the series. |
| 📦 Generates UTF-8 JSON (`title` + `tvdbId`/`imdbId`) | Compatible with Sonarr/Radarr **Custom** import lists. |
| 🕒 **GitHub Action** runs daily at 03:00 UTC | Keeps the list up-to-date without a server. |
| ⚙️ Configurable number of titles (`-n` flag) | Default = 25 but you can ask for 5, 10, 50, … |
| 🐍 Simple Python scripts | `generate_list.py` for TV, `generate_movies.py` for movies. |
| 📂 No external secrets needed | All requests are public (IMDb page & TVMaze). |

---

## 🛠️ Prerequisites

| Component | What you need |
|-----------|----------------|
| **Python 3.9+** | `python3 --version` |
| **pip** | Comes with Python; install dependencies from `requirements.txt`. |
| **Sonarr** (v3+ recommended) | For TV shows – running locally or on a NAS. |
| **Radarr** | For movies – running locally or on a NAS. |
| **GitHub account** | To host the repository and run the Action. |

---

## 📦 Installation – Running the script locally

```bash
# 1️⃣ Clone the repo
git clone https://github.com/<your-user>/imdb-top-tv-list.git
cd imdb-top-tv-list

# 2️⃣ Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3️⃣ Install required Python packages
pip install -r requirements.txt

# 4️⃣ Install Playwright browsers (required for scraping)
playwright install chromium --with-deps

# 5️⃣ Generate TV shows list (default = 25 titles)
python generate_list.py

# 6️⃣ Generate movies list (default = 25 titles, Bollywood excluded)
python generate_movies.py

# 7️⃣ Verify the output
head -n 10 top_tvshows_25.json
head -n 10 top_movies_25.json
```

---

## 📋 Output Files

| File | Description | Use with |
|------|-------------|----------|
| `top_tvshows_5.json` | Top 5 popular TV shows | Sonarr |
| `top_tvshows_10.json` | Top 10 popular TV shows | Sonarr |
| `top_tvshows_25.json` | Top 25 popular TV shows | Sonarr |
| `top_movies_5.json` | Top 5 popular movies (Bollywood excluded) | Radarr |
| `top_movies_10.json` | Top 10 popular movies (Bollywood excluded) | Radarr |
| `top_movies_25.json` | Top 25 popular movies (Bollywood excluded) | Radarr |

### JSON Format

**TV Shows (Sonarr):**
```json
[
  {"title": "One Piece", "tvdbId": 392276},
  {"title": "The Pitt", "tvdbId": 448176}
]
```

**Movies (Radarr):**
```json
[
  {"title": "Project Hail Mary", "imdbId": "tt12042730"},
  {"title": "The Super Mario Galaxy Movie", "imdbId": "tt28650488"}
]
```

---

## 🔄 GitHub Actions

The workflow runs daily at 03:00 UTC and generates all six JSON files:

1. Checks out the repository
2. Sets up Python 3.11
3. Installs dependencies
4. Installs Playwright browsers
5. Generates TV show lists (5, 10, 25)
6. Generates movie lists (5, 10, 25)
7. Commits changes if any files updated

---

## 🔧 Configuration

### Number of Titles

```bash
# Generate top 50 TV shows
python generate_list.py -n 50 -o top_tvshows_50.json

# Generate top 100 movies
python generate_movies.py -n 100 -o top_movies_100.json
```

### Custom User Agent

```bash
python generate_list.py --user-agent "Your Custom Agent/1.0"
```

---

## 🎬 About Bollywood Filtering

The movie scraper automatically excludes Bollywood films using IMDb URL parameters:
- `countries=!in` – Excludes India as country of origin
- `languages=!hi` – Excludes Hindi language films

This ensures the movie list focuses on Western/international cinema while respecting that Bollywood films have their own dedicated platforms and audiences.

---

## 📄 License

MIT License – see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

---

## 📝 Changelog

### 2026-04-06
- Added `generate_movies.py` for movie scraping
- Bollywood exclusion via IMDb URL parameters
- GitHub Actions now generates both TV and movie lists
- Updated to use Playwright for scraping (fixed WAF issues)
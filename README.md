# 📺 IMDb‑Top‑TV‑List → Sonarr

**Automated nightly generation of a JSON file that contains the top‑N popular TV series on IMDb, enriched with the TVDB ID**.  
The file is published via a GitHub Actions workflow and can be consumed by **Sonarr → Settings → Import Lists → Custom** (or TMDb/Script) to automatically add new shows to your library.

---

## 🎯 Why this repo?

- **Never miss a hit show** – every night the list is refreshed from IMDb’s “Popular TV Shows” page.  
- **Sonarr‑ready JSON** – each entry includes `title` **and** `tvdbId`, which is exactly what Sonarr’s *Custom* import list expects.  
- **Zero‑maintenance** – once set up the whole pipeline (scrape → TVDB lookup → JSON → GitHub → Sonarr) runs automatically.  
- **Fully open source** – MIT licensed, easy to fork or extend.

---

## ✨ Features

| Feature | Details |
|--------|----------|
| ✅ Scrapes the latest IMDb “Popular TV Shows” page | Handles the new IMDb layout (`ipc‑title‑link‑wrapper`). |
| 🔎 Resolves IMDb IDs to TVDB IDs via **TVMaze** (free, no API key) | Guarantees Sonarr can add the series. |
| 📦 Generates UTF‑8 JSON (`title` + `tvdbId`) | Compatible with Sonarr’s **Custom** import list. |
| 🕒 **GitHub Action** runs daily at 03:00 UTC | Keeps the list up‑to‑date without a server. |
| ⚙️ Configurable number of titles (`-n` flag) | Default = 25 but you can ask for 10, 15, 30, … |
| 🐍 Simple Python script (`generate_list.py`) | Works on any platform with Python 3.9+. |
| 📂 No external secrets needed | All requests are public (IMDb page & TVMaze). |

---

## 🛠️ Prerequisites

| Component | What you need |
|-----------|----------------|
| **Python 3.9+** | `python3 --version` |
| **pip** | Comes with Python; install dependencies from `requirements.txt`. |
| **Sonarr** (v3+ recommended) | Running locally or on a NAS. |
| **GitHub account** | To host the repository and run the Action. |
| (Optional) **TVMaze** | No API key required – the script uses the public lookup endpoint. |

---

## 📦 Installation – Running the script locally (useful for testing)

```bash
# 1️⃣ Clone the repo
git clone https://github.com/<your‑user>/imdb-top-tv-list.git
cd imdb-top-tv-list

# 2️⃣ Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3️⃣ Install required Python packages
pip install -r requirements.txt

# 4️⃣ Generate the list (default = 25 titles)
python generate_list.py

# 5️⃣ Verify the output
head -n 10 top_25.json
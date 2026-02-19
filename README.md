# Portfolio Assets Finder

A lightweight tool to **find, organize, and export portfolio-ready asset links** (and optional downloads where permitted) using structured search inputs like **brand, event, city, date, photographer, and talent**.

**Built for:** fast portfolio assembly, case-study building, and content planning  
**Best for:** creatives, agencies, stylists, MUAs, hair artists, producers

---

## What it does

- 🔎 Search across **public web sources** using your structured keywords (brand / event / location / date)
- 🧾 Save results into a clean **run folder** with exported files (CSV/JSON) for reuse
- 🗂️ Generate a **consistent folder layout** so you can paste/plan content quickly
- 🧷 Instagram support is **links-only by default** (no private scraping)

---

## How to use

- Enter a **Search Profile** (example below)
- Choose sources (e.g., **Web**, **Instagram (links-only)**)
- Run search → review results table
- Click **Export** to generate an output folder you can reuse

---

## Example Search Profile

- **Artist / Talent:** Holli Smith  
- **Agency:** Art Partner  
- **Brand / Show:** Jean Paul Gaultier (Fashion Show)  
- **Year / City:** 2025, Paris  
- **Extra Keywords:** backstage, runway, beauty, hair

---

## Output

Each run creates a timestamped folder inside `output/` (recommended) with clean exports.

---
## Live Demo

- **Live Demo:** (https://mrponyrivers-portfolio-asset-finder.streamlit.app/)
- **Local Demo:** run the Quickstart below

---

## Quickstart

### 1) Clone + install

```bash
git clone https://github.com/mrponyrivers/portfolio_asset_finder.git
cd portfolio_asset_finder

python -m venv .venv
source .venv/bin/activate   # (macOS/Linux)
# .venv\Scripts\activate    # (Windows PowerShell)

pip install -r requirements.txt

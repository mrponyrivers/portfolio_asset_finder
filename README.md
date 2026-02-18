## Quickstart (standalone)
```bash
cd portfolio_asset_finder
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# add your SerpAPI key (don't commit it)
export SERPAPI_API_KEY="YOUR_KEY"

python -m streamlit run app.py

# Portfolio Asset Finder + Organizer (Streamlit)

Searches public web sources (via SerpAPI or Bing), lets you select results, downloads open image URLs where permitted, and organizes them into a portfolio folder structure with metadata + an Instagram pack (caption/credits/hashtags).

## What it does
- Source-targeted search: Vogue / VogueRunway / brand site / Instagram links (Option 1)
- Select results in UI
- Download open images (non-Instagram) and save to:
  `output/Portfolio/{year}/{location}/{project}/{photographer}/Assets`
- Export metadata:
  - `Metadata/assets.json`
  - `Metadata/assets.csv`
  - `Metadata/links.txt`
- Generate Instagram pack:
  - `Instagram_Pack/caption.txt`
  - `Instagram_Pack/credits.txt`
  - `Instagram_Pack/hashtags.txt`

## Instagram (Option 1)
Instagram is **links-only** in Option 1. The app can find IG post/reel URLs, but does not download IG media.

## Setup
Create/activate your venv (example assumes shared venv at `~/ai-journey/.venv`):

```bash
cd ~/ai-journey/portfolio_asset_finder
source ../.venv/bin/activate
python -m pip install -r requirements.txt

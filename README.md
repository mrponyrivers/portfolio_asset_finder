## Quickstart (standalone)

```bash
git clone https://github.com/mrponyrivers/portfolio_asset_finder.git
cd portfolio_asset_finder
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# add your SerpAPI key (don't commit it)
export SERPAPI_API_KEY="YOUR_KEY"

python -m streamlit run app.py
```
Portfolio Asset Finder + Organizer (Streamlit)

Searches public web sources (via SerpAPI or Bing), lets you select results, downloads open image URLs where permitted, and organizes them into a portfolio folder structure with metadata + an Instagram pack (caption/credits/hashtags).

What it does

Source-targeted search: Vogue / VogueRunway / brand site / Instagram links (Option 1)

Select results in the UI

Download open images (non-Instagram) and save to:
output/Portfolio/{year}/{location}/{project}/{photographer}/Assets

Export metadata:

Metadata/assets.json

Metadata/assets.csv

Metadata/links.txt

Generate Instagram pack:

Instagram_Pack/caption.txt

Instagram_Pack/credits.txt

Instagram_Pack/hashtags.txt

Instagram (Option 1)

Instagram is links-only in Option 1. The app can find IG post/reel URLs, but does not download IG media.

Requirements

Python 3.9+

A SerpAPI key (recommended) or Bing Web Search API key (optional)

Setup (standalone venv)
cd portfolio_asset_finder
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export SERPAPI_API_KEY="YOUR_KEY"
python -m streamlit run app.py

Setup (shared venv option)

If you use a shared venv at ~/ai-journey/.venv:

cd ~/ai-journey/portfolio_asset_finder
source ../.venv/bin/activate
python -m pip install -r requirements.txt
export SERPAPI_API_KEY="YOUR_KEY"
python -m streamlit run app.py

Output structure

The app writes to:

output/Portfolio/{year}/{location}/{project}/{photographer}/

Assets/ downloaded images (non-Instagram)

Metadata/ assets.json, assets.csv, links.txt, post_plan.md

Instagram_Pack/ caption.txt, credits.txt, hashtags.txt

Notes / limitations

Downloads depend on whether the page exposes direct image URLs and allows access.

Some pages are JS-heavy or restricted; extraction may return few/no images.

Instagram is links-only in Option 1.

Roadmap

Option 2: add “manual IG post URL input” and packaging (still links-only), plus improved preview/selection

Better dedupe (hashing) and download reporting (why an image was skipped)

Optional deployment guide (Streamlit Cloud + secrets)



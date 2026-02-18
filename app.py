from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import streamlit as st
from slugify import slugify

from search_providers import (
    MockSearchProvider,
    BingWebSearchProvider,
    SerpApiSearchProvider,
    SearchResult,
)
from extractors import extract_image_urls_from_page
from downloader import download_image
from packer import build_project_paths, AssetRecord, export_metadata, generate_caption_files
from validate import check_image_url

st.set_page_config(page_title="Portfolio Asset Finder + Organizer", layout="wide")
st.title("Portfolio Asset Finder + Organizer")
st.caption("Option 1: source-targeted search → select → download open web images → organize + IG Pack. Instagram is links-only in Option 1.")

# ---------------- Provider ----------------
st.sidebar.header("Search Provider")
provider_choice = st.sidebar.selectbox(
    "Provider",
    ["SerpAPI (recommended)", "Bing Web Search API", "Mock (no API key)"],
    index=0,
)

if provider_choice == "Mock (no API key)":
    provider = MockSearchProvider()
elif provider_choice == "Bing Web Search API":
    provider = BingWebSearchProvider()
else:
    provider = SerpApiSearchProvider()

# ---------------- Inputs ----------------
st.sidebar.header("Project Details")
hair_artist = st.sidebar.text_input("Hair artist (metadata)", value="Holli Smith")
agency = st.sidebar.text_input("Agency (metadata)", value="Art Partner")

designer = st.sidebar.text_input("Designer / Brand (search)", value="Jean Paul Gaultier")
season = st.sidebar.text_input("Season / Collection (search)", value="Haute Couture Spring 2025")
year = st.sidebar.text_input("Year", value="2025")
location = st.sidebar.text_input("Location", value="Paris")

project = st.sidebar.text_input("Project / Event (folder)", value="Jean Paul Gaultier Show")
photographer = st.sidebar.text_input("Photographer (optional)", value="")

brand_domain = st.sidebar.text_input("Brand domain (optional)", value="", help="example: loewe.com").strip().lower()
keywords = st.sidebar.text_input("Keywords (comma separated)", value="runway, backstage, couture, show").strip()

# IG handle
st.sidebar.header("Instagram (Brand handle)")

# Optional saved handles (you can still type anything below)
if "brand_handles" not in st.session_state:
    st.session_state.brand_handles = ["", "@jpgaultierofficial", "@loewe", "@voguemagazine", "@voguerunway"]

saved = st.sidebar.selectbox("Pick saved handle (optional)", st.session_state.brand_handles, index=0)
typed = st.sidebar.text_input("Type handle (any brand)", value=saved, help="Example: @loewe or loewe")

def normalize_handle(h: str) -> str:
    h = (h or "").strip()
    if not h:
        return ""
    if not h.startswith("@"):
        h = "@" + h
    return h

ig_handle = normalize_handle(typed)

ig_mode = st.sidebar.selectbox(
    "Instagram search mode",
    ["Handle only", "Handle + show terms", "No handle (show terms only)"],
    index=1,
)

# Sources
st.sidebar.header("Sources to search")
use_instagram = st.sidebar.checkbox("Instagram (links only)", value=True)
use_vogue = st.sidebar.checkbox("Vogue.com", value=True)
use_voguerunway = st.sidebar.checkbox("VogueRunway.com", value=True)
use_brand = st.sidebar.checkbox("Brand/Designer site", value=True)

# Limits
st.sidebar.header("Search Limits")
max_results_each = st.sidebar.slider("Max results per source", 5, 30, 12)

# Download rules
st.sidebar.header("Download Rules")
min_kb = st.sidebar.slider("Skip images smaller than (KB)", 5, 250, 30)
max_images_per_page = st.sidebar.slider("Max images to try per selected page", 5, 60, 25)

# Pack
st.sidebar.header("Instagram Pack")
credits_line = st.sidebar.text_area("Credits line", value=f"Hair: {hair_artist} ({agency})")
hashtags = st.sidebar.text_area("Hashtags", value="#hair #fashion #runway #backstage #editorial")

def normalize_text(s: str) -> str:
    s = (s or "").strip().replace(",", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def mk(*parts: str) -> str:
    return normalize_text(" ".join([normalize_text(p) for p in parts if normalize_text(p)])).strip()

base_query = st.text_area("Base query (editable)", value=mk(designer, season, location, year, keywords), height=70)

# Session
if "results_by_source" not in st.session_state:
    st.session_state.results_by_source = {}
if "selected_urls" not in st.session_state:
    st.session_state.selected_urls = set()

def do_web(query: str) -> list[SearchResult]:
    return provider.search(query=query, count=max_results_each)

def do_images(query: str) -> list[SearchResult]:
    try:
        return provider.search_images(query=query, count=max_results_each)
    except Exception:
        return provider.search(query=query, count=max_results_each)

def build_queries() -> dict[str, dict[str, str]]:
    q = {}
    vogue_core = mk(designer, season, year, location, "fashion show")

    if use_vogue:
        q["Vogue.com"] = {"mode": "images", "query": mk("site:vogue.com/fashion-shows", vogue_core)}
    if use_voguerunway:
        q["VogueRunway.com"] = {"mode": "images", "query": mk("site:voguerunway.com", vogue_core)}

    if use_brand and brand_domain:
        q["Brand site"] = {"mode": "images", "query": mk(f"site:{brand_domain}", designer, season, year, "lookbook press runway")}
    elif use_brand:
        q["Brand site (web)"] = {"mode": "images", "query": mk(designer, season, year, "official site lookbook press runway", "-site:pinterest.com", "-site:tiktok.com")}

    if use_instagram:
        base_ig = "site:instagram.com (inurl:/p/ OR inurl:/reel/)"
        handle = "" if ig_handle == "(none)" else ig_handle
        if ig_mode == "Handle only":
            q["Instagram"] = {"mode": "web", "query": mk(base_ig, f"\"{handle}\"" if handle else designer)}
        elif ig_mode == "Handle + show terms":
            q["Instagram"] = {"mode": "web", "query": mk(base_ig, f"\"{handle}\"" if handle else "", mk(designer, season, year, keywords))}
        else:
            q["Instagram"] = {"mode": "web", "query": mk(base_ig, mk(designer, season, year, keywords))}
    return q

# Run search
if st.button("Search sources"):
    results_by = {}
    for name, spec in build_queries().items():
        mode = spec["mode"]
        query = spec["query"]
        try:
            results = do_images(query) if mode == "images" else do_web(query)
            results_by[name] = {"query": query, "mode": mode, "results": results}
        except Exception as e:
            results_by[name] = {"query": query, "mode": mode, "results": [], "error": str(e)}
    st.session_state.results_by_source = results_by
    st.session_state.selected_urls = set()

st.divider()

if not st.session_state.results_by_source:
    st.info("Click **Search sources**.")
    st.stop()

st.subheader("Results by source")
for source, payload in st.session_state.results_by_source.items():
    with st.expander(f"{source} — {len(payload.get('results', []))} results ({payload.get('mode')})", expanded=True):
        st.code(payload.get("query", ""))
        if payload.get("error"):
            st.error(payload["error"])
        for i, r in enumerate(payload.get("results", [])):
            checked = st.checkbox(f"Select: {r.title or r.url}", key=f"{source}_{i}")
            if checked:
                st.session_state.selected_urls.add(r.url)
            else:
                st.session_state.selected_urls.discard(r.url)
            st.write(r.url)
            if getattr(r, "thumbnail_url", ""):
                try:
                    st.image(r.thumbnail_url, width=240)
                except Exception:
                    pass

# Output folders
paths = build_project_paths(Path("output"), year, location, project, photographer)
assets_dir = paths["assets"]
meta_dir = paths["meta"]
pack_dir = paths["pack"]
st.write(f"Saving into: `{paths['root']}`")

if st.button("Download/Organize Selected"):
    selected = list(st.session_state.selected_urls)
    if not selected:
        st.warning("Select at least one result.")
        st.stop()

    # flatten results
    all_results = []
    for payload in st.session_state.results_by_source.values():
        all_results.extend(payload.get("results", []))

    records = []
    for page_url in selected:
        matched = next((rr for rr in all_results if rr.url == page_url), None)
        downloaded = []

        if "instagram.com" in page_url:
            records.append(AssetRecord(project, year, location, photographer, matched.title if matched else "(ig)", page_url, page_url, [], "Instagram link saved (links-only).", credits_line, keywords, datetime.utcnow().isoformat()))
            continue

        # try direct image first if present
        direct = getattr(matched, "image_url", "") if matched else ""
        base_name = slugify(project)[:30] or "asset"

        if direct:
            chk = check_image_url(direct)
            if chk.ok:
                res = download_image(chk.final_url, out_dir=assets_dir, base_name=base_name, min_kb=min_kb)
                if res.ok and res.filepath:
                    downloaded.append(res.filepath)

        if not downloaded:
            try:
                img_urls = extract_image_urls_from_page(page_url, max_images=max_images_per_page)
            except Exception:
                img_urls = []
            for u in img_urls:
                chk = check_image_url(u)
                if chk.ok:
                    res = download_image(chk.final_url, out_dir=assets_dir, base_name=base_name, min_kb=min_kb)
                    if res.ok and res.filepath:
                        downloaded.append(res.filepath)
                if len(downloaded) >= 8:
                    break

        records.append(AssetRecord(project, year, location, photographer, matched.title if matched else "(selected)", page_url, page_url, downloaded, "", credits_line, keywords, datetime.utcnow().isoformat()))

    export_metadata(records, meta_dir)
    generate_caption_files(pack_dir, project, year, location, photographer, credits_line, hashtags)
    st.success("Done!")

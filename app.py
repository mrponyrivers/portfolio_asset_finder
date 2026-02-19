from __future__ import annotations

from pathlib import Path
from datetime import datetime
import os
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


# =========================
# Demo profile + helpers
# =========================
SAMPLE_PROFILE = {
    "talent_name": "Holli Smith",
    "agency": "Art Partner",
    "brand": "Jean Paul Gaultier",
    "season": "Haute Couture Spring",
    "year": 2025,
    "location": "Paris",
    "project_event": "JPG Couture Spring 2025 (Paris)",
    "photographer": "",
    "brand_domain": "",
    "keywords": "backstage, runway, beauty, hair",
    "ig_handle": "jeanpaulgaultier",
    "credits_line": "Hair: Holli Smith (Art Partner)",
    "hashtags": "#hair #fashion #runway #backstage #editorial",
    "ig_mode": "Links-only (handle + show terms)",
    "sources": ["Web", "Instagram (links-only)"],
    "provider": "Mock (no API key)",
    "use_vogue": True,
    "use_voguerunway": True,
    "use_brand_site": True,
    "max_results": 10,
    "min_kb": 30,
    "max_images_per_page": 15,
}

def load_sample_profile():
    for k, v in SAMPLE_PROFILE.items():
        st.session_state[k] = v
    st.session_state["RUN_SEARCH_NOW"] = False  # just load fields

def run_demo_search():
    load_sample_profile()
    st.session_state["RUN_SEARCH_NOW"] = True  # load fields + run

def clear_results():
    # Clear stored results + selections
    st.session_state["results_by_source"] = {}
    st.session_state["selected_urls"] = set()

    # Clear per-result checkbox keys so checkmarks don't persist
    for k in list(st.session_state.keys()):
        if str(k).startswith("sel__"):
            st.session_state.pop(k, None)

    # Optional: show a small confirmation message
    st.session_state["CLEARED_NOTICE"] = True


def normalize_text(s: str) -> str:
    s = (s or "").strip().replace(",", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def mk(*parts) -> str:
    cleaned = []
    for p in parts:
        if p is None:
            continue
        if isinstance(p, int):
            p = str(p)
        p = normalize_text(str(p))
        if p:
            cleaned.append(p)
    return " ".join(cleaned).strip()

def get_provider(provider_choice: str):
    if provider_choice.startswith("Mock"):
        return MockSearchProvider()
    if provider_choice.startswith("Bing"):
        return BingWebSearchProvider()
    return SerpApiSearchProvider()

def do_search(provider_obj, mode: str, query: str, count: int) -> list[SearchResult]:
    if mode == "images":
        try:
            return provider_obj.search_images(query=query, count=count)
        except Exception:
            return provider_obj.search(query=query, count=count)
    return provider_obj.search(query=query, count=count)

def build_queries(
    base_query: str,
    sources: list[str],
    brand_domain: str,
    ig_handle: str,
    ig_mode: str,
    use_vogue: bool,
    use_voguerunway: bool,
    use_brand_site: bool,
) -> dict[str, dict[str, str]]:
    q: dict[str, dict[str, str]] = {}

    if "Web" in sources:
        if use_vogue:
            q["Vogue.com"] = {"mode": "images", "query": mk("site:vogue.com/fashion-shows", base_query)}
        if use_voguerunway:
            q["VogueRunway.com"] = {"mode": "images", "query": mk("site:voguerunway.com", base_query)}

        if use_brand_site:
            if brand_domain:
                q["Brand site"] = {"mode": "images", "query": mk(f"site:{brand_domain}", base_query, "lookbook press runway")}
            else:
                q["Brand site (web)"] = {
                    "mode": "images",
                    "query": mk(base_query, "official site lookbook press runway", "-site:pinterest.com", "-site:tiktok.com"),
                }

    if "Instagram (links-only)" in sources:
        base_ig = "site:instagram.com (inurl:/p/ OR inurl:/reel/)"
        handle = (ig_handle or "").strip().lstrip("@")

        if ig_mode == "Links-only (handle only)":
            query = mk(base_ig, f"\"{handle}\"" if handle else base_query)
        elif ig_mode == "Links-only (handle + show terms)":
            query = mk(base_ig, f"\"{handle}\"" if handle else "", base_query)
        else:
            query = mk(base_ig, base_query)

        q["Instagram"] = {"mode": "web", "query": query}

    return q


# =========================
# Streamlit page
# =========================
st.set_page_config(page_title="Portfolio Asset Finder + Organizer", layout="wide")
st.title("Portfolio Asset Finder + Organizer")
st.caption(
    "Option 1: source-targeted search → select → download open web images → organize + IG Pack. "
    "Instagram is links-only in Option 1."
)

# -------------------------
# Session state defaults
# -------------------------
defaults = {
    "provider": "Mock (no API key)",
    "brand": "",
    "season": "",
    "year": datetime.now().year,
    "location": "",
    "keywords": "",
    "sources": ["Web"],
    "talent_name": "",
    "agency": "",
    "project_event": "",
    "photographer": "",
    "brand_domain": "",
    "credits_line": "",
    "hashtags": "",
    "ig_handle": "",
    "ig_mode": "Links-only (handle + show terms)",
    "use_vogue": True,
    "use_voguerunway": True,
    "use_brand_site": True,
    "max_results": 10,
    "min_kb": 30,
    "max_images_per_page": 15,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if "results_by_source" not in st.session_state:
    st.session_state["results_by_source"] = {}
if "selected_urls" not in st.session_state:
    st.session_state["selected_urls"] = set()
if "RUN_SEARCH_NOW" not in st.session_state:
    st.session_state["RUN_SEARCH_NOW"] = False


# =========================
# Sidebar (Beginner / Advanced)
# =========================
st.sidebar.title("Portfolio Asset Finder + Organizer")

c1, c2, c3 = st.sidebar.columns(3)
c1.button("Load sample", on_click=load_sample_profile)
c2.button("Run demo", on_click=run_demo_search)
c3.button("Clear", on_click=clear_results)

st.sidebar.caption("Tip: Click **Run demo** to see results instantly without API keys.")
st.sidebar.divider()

provider_choice = st.sidebar.selectbox(
    "Search Provider",
    ["SerpAPI (recommended)", "Bing Web Search API", "Mock (no API key)"],
    key="provider",
)

# essentials
st.sidebar.text_input("Designer / Brand (search)", key="brand")
st.sidebar.text_input("Season / Collection (search)", key="season")
st.sidebar.number_input("Year", min_value=1990, max_value=2100, step=1, key="year")
st.sidebar.text_input("Location", key="location")
st.sidebar.text_input("Keywords (comma separated)", key="keywords")

st.sidebar.multiselect(
    "Sources to search",
    ["Web", "Instagram (links-only)"],
    key="sources",
)

search_clicked = st.sidebar.button("Search sources", type="primary")

with st.sidebar.expander("Advanced", expanded=False):
    st.markdown("### Project Details")
    st.text_input("Talent / Artist name (for labels)", key="talent_name")
    st.text_input("Agency (metadata)", key="agency")
    st.text_input("Run name (folder label)", key="project_event")
    st.text_input("Photographer (optional)", key="photographer")
    st.text_input("Brand domain (optional)", key="brand_domain")

    st.markdown("### Web Sources (advanced)")
    st.checkbox("Include Vogue.com", value=st.session_state["use_vogue"], key="use_vogue")
    st.checkbox("Include VogueRunway.com", value=st.session_state["use_voguerunway"], key="use_voguerunway")
    st.checkbox("Include brand site query", value=st.session_state["use_brand_site"], key="use_brand_site")

    st.markdown("### Instagram caption pack")
    st.text_input("Credits line", key="credits_line")
    st.text_area("Hashtags", key="hashtags", height=80)

    st.markdown("### Instagram (Brand handle)")
    st.text_input("Type handle (any brand)", key="ig_handle")
    st.selectbox(
        "Instagram search mode",
        ["Links-only (handle + show terms)", "Links-only (handle only)", "Links-only (show terms only)"],
        key="ig_mode",
    )

    st.markdown("### Search Limits")
    st.slider("Max results per source", 5, 30, key="max_results")

    st.markdown("### Download Rules")
    st.slider("Skip images smaller than (KB)", 5, 250, key="min_kb")
    st.slider("Max images to try per selected page", 5, 60, key="max_images_per_page")


# =========================
# Provider readiness warnings
# =========================
if provider_choice.startswith("SerpAPI") and not os.environ.get("SERPAPI_API_KEY"):
    st.sidebar.warning("SerpAPI selected but **SERPAPI_API_KEY** is not set. Use Mock or add the key in Streamlit Secrets.")
if provider_choice.startswith("Bing") and not os.environ.get("BING_API_KEY"):
    st.sidebar.warning("Bing selected but **BING_API_KEY** is not set. Use Mock or add the key in Streamlit Secrets.")


# Optional confirmation notice after clearing
if st.session_state.pop("CLEARED_NOTICE", False):
    st.success("Cleared results.")


# =========================
# Base query (editable)
# =========================
auto_query = mk(
    st.session_state["brand"],
    st.session_state["season"],
    st.session_state["year"],
    st.session_state["location"],
    st.session_state["keywords"],
    "runway backstage",
)

if "base_query" not in st.session_state or not st.session_state["base_query"].strip():
    st.session_state["base_query"] = auto_query

colq1, colq2 = st.columns([5, 1])
with colq1:
    base_query = st.text_area("Base query (editable)", key="base_query", height=70)
with colq2:
    if st.button("Rebuild"):
        st.session_state["base_query"] = auto_query
        st.rerun()


# =========================
# Search run (sidebar click OR demo click)
# =========================
run_now = bool(search_clicked) or bool(st.session_state.pop("RUN_SEARCH_NOW", False))

if run_now:
    provider_obj = get_provider(st.session_state["provider"])
    queries = build_queries(
        base_query=st.session_state["base_query"],
        sources=st.session_state["sources"],
        brand_domain=st.session_state["brand_domain"],
        ig_handle=st.session_state["ig_handle"],
        ig_mode=st.session_state["ig_mode"],
        use_vogue=st.session_state["use_vogue"],
        use_voguerunway=st.session_state["use_voguerunway"],
        use_brand_site=st.session_state["use_brand_site"],
    )

    results_by: dict[str, dict] = {}
    for name, spec in queries.items():
        mode = spec["mode"]
        query = spec["query"]
        try:
            results = do_search(provider_obj, mode=mode, query=query, count=int(st.session_state["max_results"]))
            results_by[name] = {"query": query, "mode": mode, "results": results}
        except Exception as e:
            results_by[name] = {"query": query, "mode": mode, "results": [], "error": str(e)}

    st.session_state["results_by_source"] = results_by
    st.session_state["selected_urls"] = set()

st.divider()

if not st.session_state["results_by_source"]:
    st.info("Click **Search sources** (or **Run demo**).")
    st.stop()


# =========================
# Results UI
# =========================
st.subheader("Results by source")

for source, payload in st.session_state["results_by_source"].items():
    results = payload.get("results", []) or []
    mode = payload.get("mode", "web")
    with st.expander(f"{source} — {len(results)} results ({mode})", expanded=True):
        st.code(payload.get("query", ""))

        if payload.get("error"):
            st.error(payload["error"])
            continue

        for i, r in enumerate(results):
            key = f"sel__{source}__{i}"
            current_selected = r.url in st.session_state["selected_urls"]

            checked = st.checkbox(
                f"Select: {r.title or r.url}",
                value=current_selected,
                key=key,
            )
            if checked:
                st.session_state["selected_urls"].add(r.url)
            else:
                st.session_state["selected_urls"].discard(r.url)

            st.write(r.url)
            if getattr(r, "snippet", ""):
                st.caption(r.snippet)

            thumb = getattr(r, "thumbnail_url", "") or ""
            if thumb:
                try:
                    st.image(thumb, width=240)
                except Exception:
                    pass


# =========================
# Export / Download
# =========================
st.divider()

brand = st.session_state["brand"].strip()
season = st.session_state["season"].strip()
year = str(st.session_state["year"])
location = st.session_state["location"].strip()
photographer = st.session_state["photographer"].strip()

project_event = st.session_state["project_event"].strip()
if not project_event:
    project_event = mk(brand, season, year, location) or "Untitled Project"

run_stamp = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
project_for_folder = f"{project_event}__{run_stamp}"

paths = build_project_paths(
    base_output=Path("output"),
    year=year,
    location=location or "unknown-location",
    project=project_for_folder,
    photographer=photographer or "unknown-photographer",
)

assets_dir = paths["assets"]
meta_dir = paths["meta"]
pack_dir = paths["pack"]

st.write(f"Saving into: `{paths['root']}`")

if st.button("Download / Organize Selected", type="primary"):
    selected = list(st.session_state["selected_urls"])
    if not selected:
        st.warning("Select at least one result.")
        st.stop()

    all_results: list[SearchResult] = []
    for p in st.session_state["results_by_source"].values():
        all_results.extend(p.get("results", []) or [])

    records: list[AssetRecord] = []
    min_kb = int(st.session_state["min_kb"])
    max_images_per_page = int(st.session_state["max_images_per_page"])
    credits_line = st.session_state["credits_line"]
    hashtags = st.session_state["hashtags"]
    tags_text = st.session_state["keywords"]

    for page_url in selected:
        matched = next((rr for rr in all_results if rr.url == page_url), None)
        downloaded: list[str] = []

        if "instagram.com" in page_url:
            records.append(
                AssetRecord(
                    project=project_event,
                    year=year,
                    location=location,
                    photographer=photographer,
                    title=(matched.title if matched else "(instagram)"),
                    source_url=page_url,
                    page_url=page_url,
                    downloaded_files=[],
                    notes="Instagram link saved (links-only).",
                    credit_line=credits_line,
                    tags=tags_text,
                    created_at=datetime.utcnow().isoformat(),
                )
            )
            continue

        base_name = slugify(project_event)[:30] or "asset"

        direct = getattr(matched, "image_url", "") if matched else ""
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
                if not chk.ok:
                    continue
                res = download_image(chk.final_url, out_dir=assets_dir, base_name=base_name, min_kb=min_kb)
                if res.ok and res.filepath:
                    downloaded.append(res.filepath)
                if len(downloaded) >= 8:
                    break

        records.append(
            AssetRecord(
                project=project_event,
                year=year,
                location=location,
                photographer=photographer,
                title=(matched.title if matched else "(selected)"),
                source_url=page_url,
                page_url=page_url,
                downloaded_files=downloaded,
                notes=("" if downloaded else "No downloadable images found (or skipped by rules)."),
                credit_line=credits_line,
                tags=tags_text,
                created_at=datetime.utcnow().isoformat(),
            )
        )

    export_metadata(records, meta_dir)
    generate_caption_files(pack_dir, project_event, year, location, photographer, credits_line, hashtags)

    st.success("Done! Exported downloads + metadata + Instagram pack.")
    st.code(str(paths["root"]))

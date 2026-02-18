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

from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import streamlit as st
from slugify import slugify

SearchResult
from extractors import 
extract_image_urls_from_page
from downloader import download_image
from packer import build_project_paths, 
AssetRecord, export_metadata, 
generate_caption_files
from validate import check_image_url

st.set_page_config(page_title="Portfolio Asset 
Finder + Organizer", layout="wide")
st.title("Portfolio Asset Finder + Organizer")
st.caption("Option 1: source-targeted search → 
select → download open web images → organize + 
IG Pack. Instagram is links-only in Option 1.")

st.sidebar.header("Search Provider")
provider_choice = st.sidebar.selectbox("Provider", ["SerpAPI (recommended)", "Bing Web Search API", "Mock (no API key)"], index=0)
    "Provider",
    ["SerpAPI (recommended)", "Bing Web Search API", "Mock (no API key)"],
    index=0
)

if provider_choice == "Mock (no API key)":
    provider = MockSearchProvider()
elif provider_choice == "Bing Web Search API":
    provider = BingWebSearchProvider()
else:
    provider = SerpApiSearchProvider()

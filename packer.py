from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict
from pathlib import Path
import json
import pandas as pd
from slugify import slugify
from datetime import datetime

@dataclass
class AssetRecord:
    project: str
    year: str
    location: str
    photographer: str
    title: str
    source_url: str
    page_url: str
    downloaded_files: List[str]
    notes: str = ""
    credit_line: str = ""
    tags: str = ""
    created_at: str = ""

def build_project_paths(base_output: Path, year: str, location: str, project: str, photographer: str) -> Dict[str, Path]:
    year_s = slugify(str(year))
    loc_s = slugify(location)
    proj_s = slugify(project)
    phot_s = slugify(photographer) if photographer else "unknown-photographer"

    root = base_output / "Portfolio" / year_s / loc_s / proj_s / phot_s
    assets_dir = root / "Assets"
    pack_dir = root / "Instagram_Pack"
    meta_dir = root / "Metadata"

    for d in [assets_dir, pack_dir, meta_dir]:
        d.mkdir(parents=True, exist_ok=True)

    return {"root": root, "assets": assets_dir, "pack": pack_dir, "meta": meta_dir}

def export_metadata(records: List[AssetRecord], meta_dir: Path) -> None:
    now = datetime.utcnow().isoformat()

    # JSON
    json_path = meta_dir / "assets.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in records], f, ensure_ascii=False, indent=2)

    # CSV
    csv_path = meta_dir / "assets.csv"
    df = pd.DataFrame([asdict(r) for r in records])
    df.to_csv(csv_path, index=False)

    # Links
    links_path = meta_dir / "links.txt"
    with open(links_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(r.source_url.strip() + "\n")

    # Post plan stub
    plan_path = meta_dir / "post_plan.md"
    with open(plan_path, "w", encoding="utf-8") as f:
        f.write(f"# Post Plan\n\nGenerated: {now}\n\n")
        f.write("## Carousel order idea\n")
        f.write("- 1) Strong hero image\n- 2) Detail\n- 3) BTS\n- 4) Final look\n\n")
        f.write("## Checklist\n")
        f.write("- Confirm usage/rights for each file\n- Confirm credits\n- Keep originals backed up\n")

def generate_caption_files(pack_dir: Path, project: str, year: str, location: str, photographer: str, credits: str, hashtags: str) -> None:
    caption = f"""{project} — {location} ({year})

{credits}

{hashtags}
"""
    with open(pack_dir / "caption.txt", "w", encoding="utf-8") as f:
        f.write(caption.strip() + "\n")

    with open(pack_dir / "credits.txt", "w", encoding="utf-8") as f:
        f.write((credits or "").strip() + "\n")

    with open(pack_dir / "hashtags.txt", "w", encoding="utf-8") as f:
        f.write((hashtags or "").strip() + "\n")

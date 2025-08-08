#!/usr/bin/env python3
"""
Generate README.md with a single unified table:
- Columns: Category | Name | Latest | Information
- Category: "Scientific tool" if in STEM, "Utility" if in Utilities
- Latest = latest release tag (fallback to most recent git tag; '—' if none)
- Uses GITHUB_TOKEN from GitHub Actions for higher rate limits.
"""
from datetime import date
import os
import sys
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple

# ── Config ─────────────────────────────────────────────────────────────────────
ORG = "pscedu"
PROJECT_PREFIX = "singularity"
OUTPUT = "README.md"
CURRENT_YEAR = date.today().year
API_BASE = "https://api.github.com"

STEM_REPOS = [
    "stride","nanoplot","star-fusion","filtlong","porechop","anvio","funannotate",
    "fastq-tools","meme-suite","braker2","rust","guppy","guppy-gpu","bsmap",
    "salmon","rnaview","bioformats2raw","raw2ometiff","flash","blat","bedops",
    "genemark-es","augustus","checkm","ncview","bowtie2","asciigenome","fastqc",
    "sra-toolkit","gatk","hmmer","bcftools","raxml","spades","busco","samtools",
    "bedtools","bamtools","fastani","phylip-suite","blast","viennarna","cutadapt",
    "bismark","star","prodigal","bwa","picard","hisat2","abyss","octave","tiger",
    "gent","methylpy","fasttree","vcf2maf","htslib","kraken2","aspera-connect",
    "trimmomatic",
]

UTIL_REPOS = [
    "hashdeep","dua","vim","timewarrior","libtiff-tools","wordgrinder","shellcheck",
    "pandiff","rich-cli","jq","jp","lowcharts","btop","aws-cli","cwltool","circos",
    "glances","fdupes","graphviz","browsh","hyperfine","dust","gnuplot","pandoc",
    "mc","bat","flac","visidata","octave","ncdu","lazygit","asciinema","ffmpeg",
    "imagemagick","rclone",
]

HEADER = """# List of Singularity definition files, modulefiles and more
[![Build it!](https://github.com/pscedu/singularity/actions/workflows/build.yml/badge.svg)](https://github.com/pscedu/singularity/actions/workflows/build.yml)

This repository lists the Singularity definition files and other files needed to deploy software on Bridges2 and similar systems maintained by the Pittsburgh Supercomputing Center.
"""

FOOTER = f"""---
Copyright © 2020-{CURRENT_YEAR} Pittsburgh Supercomputing Center. All Rights Reserved.

The [Biomedical Applications Group](https://www.psc.edu/biomedical-applications/) at the [Pittsburgh Supercomputing Center](https://www.psc.edu) in the [Mellon College of Science](https://www.cmu.edu/mcs/) at [Carnegie Mellon University](https://www.cmu.edu).
"""

# ── GitHub API session ─────────────────────────────────────────────────────────
def gh_session() -> requests.Session:
    s = requests.Session()
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        s.headers["Authorization"] = f"Bearer {token}"
    s.headers["Accept"] = "application/vnd.github+json"
    s.headers["X-GitHub-Api-Version"] = "2022-11-28"
    return s

SESSION = gh_session()

def latest_tag_for(repo: str) -> str:
    """
    Return latest release tag; if no releases, fallback to most recent git tag; else '—'.
    """
    full = f"{ORG}/{PROJECT_PREFIX}-{repo}"
    try:
        r = SESSION.get(f"{API_BASE}/repos/{full}/releases/latest", timeout=10)
        if r.status_code == 200:
            data = r.json()
            tag = (data.get("tag_name") or data.get("name") or "").strip()
            if tag:
                return tag
        r = SESSION.get(f"{API_BASE}/repos/{full}/tags", params={"per_page": 1}, timeout=10)
        if r.status_code == 200 and isinstance(r.json(), list) and r.json():
            tag = (r.json()[0].get("name") or "").strip()
            if tag:
                return tag
        if r.status_code == 403 and r.headers.get("X-RateLimit-Remaining") == "0":
            return "rate-limited"
    except requests.RequestException:
        pass
    return "—"

def build_row(category_label: str, repo: str, latest: str) -> str:
    base = f"https://github.com/{ORG}/{PROJECT_PREFIX}-{repo}"
    return (
        f"| {category_label} | [{repo}]({base}) | {latest} | "
        f"![Status]({base}/actions/workflows/main.yml/badge.svg)"
        f"![Status]({base}/actions/workflows/pretty.yml/badge.svg)"
    )

def unified_catalog() -> List[Tuple[str, str]]:
    """
    Return a list of (CategoryLabel, repo) tuples with no duplicates.
    If a repo appears in both lists, prefer 'Scientific tool'.
    """
    m: Dict[str, str] = {}
    for r in STEM_REPOS:
        m[r] = "Scientific tool"
    for r in UTIL_REPOS:
        m.setdefault(r, "Utility")  # don't override STEM label if duplicate
    return sorted(((cat, r) for r, cat in m.items()), key=lambda x: (x[0], x[1]))

def write_table(out) -> None:
    out.write("| Category | Name | Latest | Information |\n")
    out.write("| --- | --- | --- | --- |\n")

    items = unified_catalog()
    tag_map: Dict[str, str] = {}

    # Fetch tags concurrently
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(latest_tag_for, repo): (cat, repo) for cat, repo in items}
        for fut in as_completed(futures):
            cat, repo = futures[fut]
            try:
                tag_map[repo] = fut.result()
            except Exception as e:
                print(f"[warn] {repo}: {e}", file=sys.stderr)
                tag_map[repo] = "—"

    for cat, repo in items:
        out.write(build_row(cat, repo, tag_map.get(repo, "—")))

def main() -> None:
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(HEADER)
        write_table(f)
        f.write(FOOTER)

if __name__ == "__main__":
    main()

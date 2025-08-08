#!/usr/bin/env python3
"""
===============================================================================
Script Name: script.py
Author: Pittsburgh Supercomputing Center (PSC)
Description:
    This script generates two files containing metadata for Singularity
    definition files and related repositories:

    1. README.md
       - Markdown table for GitHub with the following columns:
         Category | Name | Latest | Information
       - "Category" is based on the repository's type:
            * Scientific tool  → Listed in STEM_REPOS
            * Utility          → Listed in UTIL_REPOS
            * Remote Desktop Application → Listed in VIZ_REPOS
       - "Name" is a Markdown link to the repository.
       - "Latest" is the latest GitHub release tag (or most recent git tag).
       - "Information" contains workflow status badges for CI pipelines.

    2. data.tsv
       - Tab-separated version of the same table:
         Category \t Name \t Latest \t Information
       - "Information" contains the same workflow status badges in Markdown.

Functionality:
    - Fetches the latest release tag (or most recent git tag if no release).
    - Uses the GitHub REST API (v3) with optional authentication.
    - Runs concurrent HTTP requests with ThreadPoolExecutor for efficiency.
    - Sorts table rows alphabetically by repository name (case-insensitive).
    - Skips duplicate category assignments with priority order:
         1. Scientific tool
         2. Utility
         3. Remote Desktop Application

Requirements:
    - Python 3.7+
    - requests library (pip install requests)
    - Optional: Set environment variable GITHUB_TOKEN to increase API limits.

Environment Variables:
    GITHUB_TOKEN   GitHub personal access token for higher rate limits.

Usage:
    python script.py

Outputs:
    README.md   → Human-readable Markdown table for GitHub.
    data.tsv    → Machine-readable TSV file with the same contents.

Notes:
    - The Information column contains CI workflow status badges only.
    - Issues badge has been removed as per customization request.
===============================================================================
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
TSV_OUTPUT = "data.tsv"
CURRENT_YEAR = date.today().year
API_BASE = "https://api.github.com"

STEM_REPOS = [
    "stride",
    "nanoplot",
    "star-fusion",
    "filtlong",
    "porechop",
    "anvio",
    "funannotate",
    "fastq-tools",
    "meme-suite",
    "braker2",
    "rust",
    "guppy",
    "guppy-gpu",
    "bsmap",
    "salmon",
    "rnaview",
    "bioformats2raw",
    "raw2ometiff",
    "flash",
    "blat",
    "bedops",
    "genemark-es",
    "augustus",
    "checkm",
    "ncview",
    "bowtie2",
    "asciigenome",
    "fastqc",
    "sra-toolkit",
    "gatk",
    "hmmer",
    "bcftools",
    "raxml",
    "spades",
    "busco",
    "samtools",
    "bedtools",
    "bamtools",
    "fastani",
    "phylip-suite",
    "blast",
    "viennarna",
    "cutadapt",
    "bismark",
    "star",
    "prodigal",
    "bwa",
    "picard",
    "hisat2",
    "abyss",
    "octave",
    "tiger",
    "gent",
    "methylpy",
    "fasttree",
    "vcf2maf",
    "htslib",
    "kraken2",
    "aspera-connect",
    "trimmomatic",
]

UTIL_REPOS = [
    "hashdeep",
    "dua",
    "vim",
    "timewarrior",
    "libtiff-tools",
    "wordgrinder",
    "shellcheck",
    "pandiff",
    "rich-cli",
    "jq",
    "jp",
    "lowcharts",
    "btop",
    "aws-cli",
    "cwltool",
    "circos",
    "glances",
    "fdupes",
    "graphviz",
    "browsh",
    "hyperfine",
    "dust",
    "gnuplot",
    "pandoc",
    "mc",
    "bat",
    "flac",
    "visidata",
    "octave",
    "ncdu",
    "lazygit",
    "asciinema",
    "ffmpeg",
    "imagemagick",
    "rclone",
]

# Visualization apps to be labeled as "Remote Desktop Application"
VIZ_REPOS = ["gimp", "inkscape"]

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
    Handles rate limiting by returning 'rate-limited' if X-RateLimit-Remaining == 0.
    """
    full = f"{ORG}/{PROJECT_PREFIX}-{repo}"
    try:
        # Try latest release
        r = SESSION.get(f"{API_BASE}/repos/{full}/releases/latest", timeout=10)
        if r.status_code == 200:
            data = r.json()
            tag = (data.get("tag_name") or data.get("name") or "").strip()
            if tag:
                return tag

        # Fallback: most recent tag
        r = SESSION.get(
            f"{API_BASE}/repos/{full}/tags", params={"per_page": 1}, timeout=10
        )
        if r.status_code == 200 and isinstance(r.json(), list) and r.json():
            tag = (r.json()[0].get("name") or "").strip()
            if tag:
                return tag

        # Rate limit hint
        if r.status_code == 403 and r.headers.get("X-RateLimit-Remaining") == "0":
            return "rate-limited"
    except requests.RequestException:
        pass
    return "—"


def build_row(category_label: str, repo: str, latest: str) -> str:
    base = f"https://github.com/{ORG}/{PROJECT_PREFIX}-{repo}"
    # Include workflow badges; if a workflow doesn't exist, GitHub returns a neutral badge.
    return (
        f"| {category_label} | [{repo}]({base}) | {latest} | "
        f"![Status]({base}/actions/workflows/main.yml/badge.svg)"
        f"![Status]({base}/actions/workflows/pretty.yml/badge.svg) |\n"
    )


def unified_catalog() -> List[Tuple[str, str]]:
    """
    Return a list of (CategoryLabel, repo) tuples with no duplicates.
    Priority if a repo appears in multiple lists:
      1. Scientific tool
      2. Utility
      3. Remote Desktop Application
    Sorted alphabetically by repo name (case-insensitive).
    """
    m: Dict[str, str] = {}
    for r in STEM_REPOS:
        m[r] = "Scientific tool"
    for r in UTIL_REPOS:
        m.setdefault(r, "Utility")
    for r in VIZ_REPOS:
        m.setdefault(r, "Remote Desktop Application")
    return sorted(((cat, r) for r, cat in m.items()), key=lambda x: x[1].lower())


def write_tables() -> None:
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

    # Write README.md
    with open(OUTPUT, "w", encoding="utf-8") as md:
        md.write(HEADER)
        md.write("| Category | Name | Latest | Information |\n")
        md.write("| --- | --- | --- | --- |\n")
        for cat, repo in items:
            md.write(build_row(cat, repo, tag_map.get(repo, "—")))
        md.write(FOOTER)

    # Write data.tsv
    with open(TSV_OUTPUT, "w", encoding="utf-8") as tsv:
        tsv.write("Category\tName\tLatest\tInformation\n")
        for cat, repo in items:
            base = f"https://github.com/{ORG}/{PROJECT_PREFIX}-{repo}"
            info = (
                f"![Status]({base}/actions/workflows/main.yml/badge.svg) "
                f"![Status]({base}/actions/workflows/pretty.yml/badge.svg)"
            )
            tsv.write(f"{cat}\t{repo}\t{tag_map.get(repo, '—')}\t{info}\n")


def main() -> None:
    write_tables()


if __name__ == "__main__":
    main()

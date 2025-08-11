#!/usr/bin/env python3
"""
===============================================================================
Script Name: script.py
Author: Pittsburgh Supercomputing Center (PSC)
Description:
    Generates two files containing metadata for Singularity-related repositories:

    README.md and data.tsv with columns:
        Category | Name | Latest | Last Commit | Container | Build ready | Publishing ready
===============================================================================
"""

from datetime import date
import os
import sys
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional

# ── Config ─────────────────────────────────────────────────────────────────────
ORG = "pscedu"
PROJECT_PREFIX = "singularity"
OUTPUT = "README.md"
TSV_OUTPUT = "data.tsv"
CURRENT_YEAR = date.today().year
API_BASE = "https://api.github.com"

STEM_REPOS = [
    "stride", "nanoplot", "star-fusion", "filtlong", "porechop", "anvio",
    "funannotate", "fastq-tools", "meme-suite", "braker2", "rust", "guppy",
    "guppy-gpu", "bsmap", "salmon", "rnaview", "bioformats2raw", "raw2ometiff",
    "flash", "blat", "bedops", "genemark-es", "augustus", "checkm", "ncview",
    "bowtie2", "asciigenome", "fastqc", "sra-toolkit", "gatk", "hmmer",
    "bcftools", "raxml", "spades", "busco", "samtools", "bedtools", "bamtools",
    "fastani", "phylip-suite", "blast", "viennarna", "cutadapt", "bismark",
    "star", "prodigal", "bwa", "picard", "hisat2", "abyss", "octave", "tiger",
    "gent", "methylpy", "fasttree", "vcf2maf", "htslib", "kraken2",
    "aspera-connect", "trimmomatic",
]

UTIL_REPOS = [
    "hashdeep", "dua", "vim", "libtiff-tools", "wordgrinder",
    "shellcheck", "pandiff", "rich-cli", "jq", "jp", "lowcharts", "btop",
    "aws-cli", "cwltool", "circos", "glances", "fdupes", "graphviz", "browsh",
    "hyperfine", "dust", "gnuplot", "pandoc", "mc", "bat", "flac", "visidata",
    "octave", "ncdu", "lazygit", "asciinema", "ffmpeg", "imagemagick", "rclone",
]

VIZ_REPOS = ["gimp", "inkscape"]

HEADER = """# List of Singularity definition files, modulefiles and more
[![Build it!](https://github.com/pscedu/singularity/actions/workflows/build.yml/badge.svg)](https://github.com/pscedu/singularity/actions/workflows/build.yml)

This repository lists the Singularity definition files and other files needed to deploy software on Bridges2 and similar systems maintained by the Pittsburgh Supercomputing Center.
"""

FOOTER = f"""---
Copyright © 2020-{CURRENT_YEAR} Pittsburgh Supercomputing Center. All Rights Reserved.
"""


def gh_session() -> requests.Session:
    s = requests.Session()
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        s.headers["Authorization"] = f"Bearer {token}"
    s.headers["Accept"] = "application/vnd.github+json"
    return s


SESSION = gh_session()


# ── GitHub API helpers ─────────────────────────────────────────────────────────
def release_info_for(full_repo: str) -> Tuple[str, Optional[str]]:
    """Get latest tag & container status (True/False/None)."""
    try:
        r = SESSION.get(f"{API_BASE}/repos/{full_repo}/releases/latest", timeout=10)
        if r.status_code == 200:
            data = r.json()
            tag = (data.get("tag_name") or data.get("name") or "").strip() or "—"
            sif_found = any(
                (asset.get("name") or "").lower().endswith(".sif")
                for asset in data.get("assets", []) or []
            )
            return tag, ("True" if sif_found else "False")
        r = SESSION.get(
            f"{API_BASE}/repos/{full_repo}/tags", params={"per_page": 1}, timeout=10
        )
        if r.status_code == 200 and isinstance(r.json(), list) and r.json():
            tag = (r.json()[0].get("name") or "").strip() or "—"
            return tag, None
    except requests.RequestException:
        pass
    return "—", None


def last_commit_date_for(full_repo: str) -> str:
    """Get date of last commit (YYYY-MM-DD)."""
    try:
        r = SESSION.get(
            f"{API_BASE}/repos/{full_repo}/commits", params={"per_page": 1}, timeout=10
        )
        if r.status_code == 200 and isinstance(r.json(), list) and r.json():
            commit = r.json()[0]
            date_str = (
                commit.get("commit", {}).get("committer", {}).get("date")
                or commit.get("commit", {}).get("author", {}).get("date")
                or ""
            ).strip()
            if date_str:
                return date_str.split("T")[0]  # Keep only YYYY-MM-DD
            return "—"
    except requests.RequestException:
        pass
    return "—"


def workflow_status(full_repo: str, workflow_file: str) -> str:
    """Return True if latest run of workflow_file succeeded, else False."""
    try:
        r = SESSION.get(
            f"{API_BASE}/repos/{full_repo}/actions/workflows/{workflow_file}/runs",
            params={"per_page": 1},
            timeout=10,
        )
        if r.status_code == 200:
            runs = r.json().get("workflow_runs", [])
            if runs:
                return "True" if runs[0].get("conclusion") == "success" else "False"
    except requests.RequestException:
        pass
    return "False"


# ── Table helpers ──────────────────────────────────────────────────────────────
def format_status(value: Optional[str]) -> str:
    """Return emoji check/cross for True/False, else the original string."""
    if value == "True":
        return "✅"
    elif value == "False":
        return "❌"
    elif value is None:
        return "None"
    return value

def build_row(
    category_label: str,
    repo: str,
    latest: str,
    last_commit: str,
    container_status: Optional[str],
    build_ready: str,
    publish_ready: str,
) -> str:
    base = f"https://github.com/{ORG}/{PROJECT_PREFIX}-{repo}"
    container_display = format_status(container_status)
    return (
        f"| {category_label} | [{repo}]({base}) | {latest} | {last_commit} | "
        f"{container_display} | {format_status(build_ready)} | {format_status(publish_ready)} |\n"
    )


def unified_catalog() -> List[Tuple[str, str]]:
    m: Dict[str, str] = {}
    for r in STEM_REPOS:
        m[r] = "Scientific tool"
    for r in UTIL_REPOS:
        m.setdefault(r, "Utility")
    for r in VIZ_REPOS:
        m.setdefault(r, "Remote Desktop Application")
    return sorted(((cat, r) for r, cat in m.items()), key=lambda x: x[1].lower())


# ── Main logic ─────────────────────────────────────────────────────────────────
def write_tables() -> None:
    items = unified_catalog()
    latest_map, commit_map, container_map, build_map, publish_map = {}, {}, {}, {}, {}

    def fetch_all(repo: str):
        full = f"{ORG}/{PROJECT_PREFIX}-{repo}"
        latest_tag, container_status = release_info_for(full)
        last_commit = last_commit_date_for(full)
        build_ready = workflow_status(full, "main.yml")
        publish_ready = workflow_status(full, "pretty.yml")
        return latest_tag, container_status, last_commit, build_ready, publish_ready

    with ThreadPoolExecutor(max_workers=16) as ex:
        futures = {ex.submit(fetch_all, repo): (cat, repo) for cat, repo in items}
        for fut in as_completed(futures):
            cat, repo = futures[fut]
            try:
                (
                    latest_tag,
                    container_status,
                    last_commit,
                    build_ready,
                    publish_ready,
                ) = fut.result()
                latest_map[repo] = latest_tag
                container_map[repo] = container_status
                commit_map[repo] = last_commit
                build_map[repo] = build_ready
                publish_map[repo] = publish_ready
            except Exception as e:
                print(f"[warn] {repo}: {e}", file=sys.stderr)
                latest_map[repo] = "—"
                container_map[repo] = None
                commit_map[repo] = "—"
                build_map[repo] = "False"
                publish_map[repo] = "False"

    # README.md
    with open(OUTPUT, "w", encoding="utf-8") as md:
        md.write(HEADER)
        md.write(
            "| Category | Name | Latest | Last Commit | Container | Build ready | Publishing ready |\n"
        )
        md.write("| --- | --- | --- | --- | --- | --- | --- |\n")
        for cat, repo in items:
            md.write(
                build_row(
                    cat,
                    repo,
                    latest_map[repo],
                    commit_map[repo],
                    container_map[repo],
                    build_map[repo],
                    publish_map[repo],
                )
            )
        md.write(FOOTER)

    # data.tsv
    with open(TSV_OUTPUT, "w", encoding="utf-8") as tsv:
        tsv.write(
            "Category\tName\tLatest\tLast Commit\tContainer\tBuild ready\tPublishing ready\n"
        )
        for cat, repo in items:
            container_display = (
                container_map[repo] if container_map[repo] is not None else "None"
            )
            tsv.write(
                f"{cat}\t{repo}\t{latest_map[repo]}\t{commit_map[repo]}\t{container_display}\t{build_map[repo]}\t{publish_map[repo]}\n"
            )


def main() -> None:
    write_tables()


if __name__ == "__main__":
    main()

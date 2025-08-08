#!/usr/bin/env python3
"""
Generate README.md with repo table:
- Columns: Name | Latest | Information
- Latest = latest release tag (fallback to most recent git tag; '—' if none)
- Uses GITHUB_TOKEN from GitHub Actions for higher rate limits.
"""
from datetime import date
import os
import sys
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Config ─────────────────────────────────────────────────────────────────────
ORG = "pscedu"
PROJECT_PREFIX = "singularity"
OUTPUT = "README.md"
CURRENT_YEAR = date.today().year
API_BASE = "https://api.github.com"

CATEGORIES = {
    "STEM": [
        "stride","nanoplot","star-fusion","filtlong","porechop","anvio","funannotate",
        "fastq-tools","meme-suite","braker2","rust","guppy","guppy-gpu","bsmap",
        "salmon","rnaview","bioformats2raw","raw2ometiff","flash","blat","bedops",
        "genemark-es","augustus","checkm","ncview","bowtie2","asciigenome","fastqc",
        "sra-toolkit","gatk","hmmer","bcftools","raxml","spades","busco","samtools",
        "bedtools","bamtools","fastani","phylip-suite","blast","viennarna","cutadapt",
        "bismark","star","prodigal","bwa","picard","hisat2","abyss","octave","tiger",
        "gent","methylpy","fasttree","vcf2maf","htslib","kraken2","aspera-connect",
        "trimmomatic",
    ],
    "Utilities": [
        "hashdeep","dua","vim","timewarrior","libtiff-tools","wordgrinder","shellcheck",
        "pandiff","rich-cli","jq","jp","lowcharts","btop","aws-cli","cwltool","circos",
        "glances","fdupes","graphviz","browsh","hyperfine","dust","gnuplot","pandoc",
        "mc","bat","flac","visidata","octave","ncdu","lazygit","asciinema","ffmpeg",
        "imagemagick","rclone",
    ],
}

HEADER = """# List of Singularity definition files, modulefiles and more
[![Build it!](https://github.com/pscedu/singularity/actions/workflows/build.yml/badge.svg)](https://github.com/pscedu/singularity/actions/workflows/build.yml)

This repository lists the Singularity definition files and other files needed to deploy software on Bridges2 and similar systems maintained by PSC.
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
        # Try latest release
        r = SESSION.get(f"{API_BASE}/repos/{full}/releases/latest", timeout=10)
        if r.status_code == 200:
            data = r.json()
            tag = (data.get("tag_name") or data.get("name") or "").strip()
            if tag:
                return tag
        # If not found or empty, try tags endpoint (first item = most recent)
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

def build_row(repo: str, latest: str) -> str:
    base = f"https://github.com/{ORG}/{PROJECT_PREFIX}-{repo}"
    return (
        f"| [{repo}]({base}) | {latest} | "
        f"![Status]({base}/actions/workflows/main.yml/badge.svg)"
        f"![Status]({base}/actions/workflows/pretty.yml/badge.svg)"
        f"![Issues](https://img.shields.io/github/issues/{ORG}/{PROJECT_PREFIX}-{repo})"
        f"![Stars](https://img.shields.io/github/stars/{ORG}/{PROJECT_PREFIX}-{repo}) |\n"
    )

def write_category(out, title: str, repos: list[str]) -> None:
    out.write(f"\n## {title}\n")
    out.write("| Name | Latest | Information |\n")
    out.write("| --- | --- | --- |\n")

    repos_sorted = sorted(set(repos))
    tag_map: dict[str, str] = {}

    # Fetch latest tags concurrently
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(latest_tag_for, r): r for r in repos_sorted}
        for fut in as_completed(futures):
            repo = futures[fut]
            try:
                tag_map[repo] = fut.result()
            except Exception as e:
                print(f"[warn] {repo}: {e}", file=sys.stderr)
                tag_map[repo] = "—"

    for repo in repos_sorted:
        out.write(build_row(repo, tag_map.get(repo, "—")))

def main() -> None:
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(HEADER)
        for title, repos in CATEGORIES.items():
            write_category(f, title, repos)
        f.write(FOOTER)

if __name__ == "__main__":
    main()

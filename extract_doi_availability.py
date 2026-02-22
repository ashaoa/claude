"""
Extract Data Availability sections from DOI full-text pages.

Handles headings such as:
  - Data Availability
  - Data availability
  - Data Availability Statement
  - Data and Code Availability
  - Availability of Data and Materials

Improvements over the original:
  - Concurrent HTTP requests (ThreadPoolExecutor) for speed
  - Retry with exponential back-off for reliability
  - Resume support — skips DOIs already written to the output file
  - Incremental output flush — crash-safe
  - Structured logging (console + doi_extraction.log)
  - Richer heading detection (h1–h5, nested-text fallback)
  - Multiple publisher URL strategies (medrxiv, biorxiv, generic DOI)
"""

import csv
import logging
import os
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from bs4 import BeautifulSoup


# ─── Configuration ────────────────────────────────────────────────────────────

MAX_WORKERS  = 5      # parallel HTTP workers
SLEEP_S      = 0.5   # polite delay (seconds) per worker after each request
MAX_RETRIES  = 3
RETRY_DELAYS = [2, 4, 8]   # seconds between successive retries

# Heading patterns checked in priority order (most specific first)
AVAILABILITY_PATTERNS = [
    r"data\s+availability\s+statement",
    r"data\s+and\s+code\s+availability",
    r"availability\s+of\s+data\s+and\s+(?:materials?|code)",
    r"data\s+availability",
    r"availability\s+of\s+data",
]

HEADING_TAGS = ["h1", "h2", "h3", "h4", "h5"]


# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(message)s",
    handlers=[
        logging.FileHandler("doi_extraction.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# ─── Heading matching ─────────────────────────────────────────────────────────

def is_availability_heading(text: str) -> bool:
    """Return True if *text* matches any data-availability heading pattern."""
    t = text.strip().lower()
    return any(re.search(p, t) for p in AVAILABILITY_PATTERNS)


# ─── HTTP fetch with retry ────────────────────────────────────────────────────

def fetch(url: str) -> bytes:
    """GET *url* and return raw bytes; retries with exponential back-off."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (research; contact: you@example.com)"},
    )
    delays = [0] + RETRY_DELAYS          # first attempt has no pre-delay
    for attempt, delay in enumerate(delays):
        if delay:
            time.sleep(delay)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 404, 410):
                raise                    # no point retrying client errors
            if attempt == MAX_RETRIES:
                raise
            log.debug("HTTP %s fetching %s — retry %s", exc.code, url, attempt + 1)
        except OSError:
            if attempt == MAX_RETRIES:
                raise
            log.debug("Network error fetching %s — retry %s", url, attempt + 1)


# ─── HTML parsing ─────────────────────────────────────────────────────────────

def extract_from_soup(soup: BeautifulSoup) -> str:
    """
    Locate the data-availability heading and return the following text block.

    Strategy 1: heading whose .string matches (fast path).
    Strategy 2: heading whose full .get_text() matches (handles nested <a> etc.).
    """
    header = soup.find(
        HEADING_TAGS,
        string=lambda s: s and is_availability_heading(s),
    )

    if not header:
        for tag in HEADING_TAGS:
            for el in soup.find_all(tag):
                if is_availability_heading(el.get_text()):
                    header = el
                    break
            if header:
                break

    if not header:
        return ""

    # Collect siblings until the next heading at the same or higher level
    stop_tags = set(HEADING_TAGS[: HEADING_TAGS.index(header.name) + 1])
    parts = []
    for sib in header.find_next_siblings():
        if sib.name in stop_tags:
            break
        txt = sib.get_text(" ", strip=True)
        if txt:
            parts.append(txt)

    return " ".join(parts).strip()


# ─── DOI helpers ──────────────────────────────────────────────────────────────

def clean_doi(raw: str) -> str:
    """Strip URL prefixes and return a bare DOI string."""
    return re.sub(r"https?://(dx\.)?doi\.org/", "", str(raw)).strip()


def candidate_urls(doi: str) -> list:
    """
    Return an ordered list of full-text URLs to try for *doi*.

    medrxiv/biorxiv DOIs (prefix 10.1101) get specific fast paths;
    everything falls back to the generic doi.org resolver.
    """
    urls = []
    if doi.startswith("10.1101"):
        versioned = doi if re.search(r"v\d+$", doi) else doi + "v1"
        urls += [
            f"https://www.medrxiv.org/content/{versioned}.full",
            f"https://www.biorxiv.org/content/{versioned}.full",
        ]
    urls.append(f"https://doi.org/{doi}")
    return urls


def extract_data_availability(raw_doi: str) -> str:
    """Return the data-availability text for *raw_doi*, or '' on failure."""
    doi = clean_doi(raw_doi)
    if not doi:
        return ""

    for url in candidate_urls(doi):
        try:
            html = fetch(url)
            soup = BeautifulSoup(html, "html.parser")
            text = extract_from_soup(soup)
            if text:
                return text
        except Exception as exc:
            log.debug("Skip %s — %s", url, exc)

    return ""


# ─── Resume support ───────────────────────────────────────────────────────────

def already_processed(output_file: str, doi_col: str) -> set:
    """Return the set of DOIs already written to *output_file*."""
    done: set = set()
    if not os.path.exists(output_file):
        return done
    try:
        with open(output_file, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                doi = row.get(doi_col, "").strip()
                if doi:
                    done.add(doi)
    except Exception:
        pass
    return done


# ─── Main CSV processor ───────────────────────────────────────────────────────

def process_csv(
    input_file: str,
    output_file: str,
    doi_column_name: str = "doi",
    sleep_s: float = SLEEP_S,
    max_workers: int = MAX_WORKERS,
) -> None:
    """
    Read *input_file*, extract data-availability text for each DOI,
    and write results to *output_file*.

    Supports resuming: DOIs already present in *output_file* are skipped.
    Results are flushed after every row so a crash loses minimal work.
    """
    # ── Read input ────────────────────────────────────────────────────────────
    with open(input_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("Input CSV has no header row.")
        if doi_column_name not in reader.fieldnames:
            raise ValueError(
                f"Column '{doi_column_name}' not found. "
                f"Available columns: {list(reader.fieldnames)}"
            )
        fieldnames = list(reader.fieldnames) + ["data_availability"]
        all_rows   = list(reader)

    # ── Resume: find what's already done ──────────────────────────────────────
    done_dois = already_processed(output_file, doi_column_name)
    pending   = [r for r in all_rows
                 if r.get(doi_column_name, "").strip() not in done_dois]

    log.info(
        "Total: %d | Already processed: %d | Remaining: %d",
        len(all_rows), len(done_dois), len(pending),
    )

    if not pending:
        log.info("Nothing left to process.")
        return

    # ── Open output (fresh or append) ─────────────────────────────────────────
    resuming     = bool(done_dois)
    out_lock     = Lock()

    with open(
        output_file,
        "a" if resuming else "w",
        newline="",
        encoding="utf-8",
    ) as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, extrasaction="ignore")
        if not resuming:
            writer.writeheader()

        # ── Worker function ───────────────────────────────────────────────────
        def worker(row: dict) -> tuple:
            doi_val = row.get(doi_column_name, "")
            result  = extract_data_availability(doi_val)
            time.sleep(sleep_s)
            return row, result

        # ── Concurrent execution ──────────────────────────────────────────────
        processed = 0
        total     = len(pending)

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(worker, row): row for row in pending}
            for future in as_completed(futures):
                processed += 1
                try:
                    row, availability = future.result()
                    row["data_availability"] = availability
                    status = "found" if availability else "empty"
                except Exception as exc:
                    row = futures[future]
                    row["data_availability"] = ""
                    status = "error"
                    log.error("Error on %s: %s", row.get(doi_column_name, "?"), exc)

                with out_lock:
                    writer.writerow(row)
                    outfile.flush()          # persist immediately

                log.info(
                    "[%d/%d] %-5s %s",
                    processed, total, status, row.get(doi_column_name, ""),
                )

    log.info("Done. Output saved to: %s", output_file)


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    process_csv(
        input_file      = "input.csv",
        output_file     = "output.csv",
        doi_column_name = "doi",    # change if your column header differs
        sleep_s         = 0.5,      # polite delay per worker between requests
        max_workers     = 5,        # parallel workers (increase carefully)
    )

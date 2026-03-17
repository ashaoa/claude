"""
Extract the Data Availability Statement from a DOI article URL.

Install dependencies (Replit Shell):
    pip install requests beautifulsoup4 playwright
    playwright install chromium
"""

import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Strategy 1: requests + BeautifulSoup (fast, works for SSR pages)
# ---------------------------------------------------------------------------

def _extract_with_requests(url: str) -> tuple[str, str] | None:
    """Returns (heading, content) or None if not found."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    resp = requests.get(url, headers=headers, allow_redirects=True, timeout=30)
    resp.raise_for_status()
    return _parse_html(resp.text)


def _parse_html(html: str) -> tuple[str, str] | None:
    """Parse raw HTML and return (heading_text, content) or None."""
    soup = BeautifulSoup(html, "html.parser")

    heading_tag = None
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5"]):
        text = tag.get_text(strip=True).lower()
        if "data availability" in text or "data statement" in text:
            heading_tag = tag
            break

    if not heading_tag:
        return None

    heading_text = heading_tag.get_text(strip=True)
    tag_level = int(heading_tag.name[1])

    # --- Strategy A: next siblings until next heading ---
    content_parts = []
    for sibling in heading_tag.find_next_siblings():
        name = sibling.name
        if name and name[0] == "h" and name[1:].isdigit() and int(name[1]) <= tag_level:
            break
        text = sibling.get_text(separator=" ", strip=True)
        if text:
            content_parts.append(text)

    if content_parts:
        return heading_text, "\n".join(content_parts).strip()

    # --- Strategy B: parent container text (minus heading) ---
    parent = heading_tag.find_parent(["section", "article", "div"])
    if parent:
        full_text = parent.get_text(separator=" ", strip=True)
        # Remove the heading text from the start
        content = full_text.replace(heading_text, "", 1).strip()
        if content:
            return heading_text, content

    return heading_text, ""


# ---------------------------------------------------------------------------
# Strategy 2: Playwright (handles JavaScript-rendered / React / MUI pages)
# ---------------------------------------------------------------------------

def _ensure_playwright_browser() -> None:
    """Auto-installs Chromium if not yet downloaded."""
    import subprocess, sys  # noqa: PLC0415
    print("[playwright] Installing Chromium browser (one-time setup)...")
    # Use sys.executable so it works even when 'playwright' is not in PATH (e.g. Replit)
    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True,
        capture_output=False,
    )
    print("[playwright] Chromium installed successfully.")


def _extract_with_playwright(url: str) -> tuple[str, str] | None:
    """
    Uses a headless Chromium browser to render the page, then parses the HTML.
    Requires: pip install playwright  (browser is auto-downloaded on first run)
    """
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    def _launch_and_fetch(p):
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=60_000)
        try:
            page.wait_for_selector("h2, h3", timeout=15_000)
        except Exception:
            pass
        html = page.content()
        browser.close()
        return html

    with sync_playwright() as p:
        try:
            html = _launch_and_fetch(p)
        except Exception as e:
            if "Executable doesn't exist" in str(e):
                _ensure_playwright_browser()
                html = _launch_and_fetch(p)
            else:
                raise

    return _parse_html(html)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def extract_data_availability_statement(doi_url: str) -> dict:
    """
    Extracts the Data Availability Statement from a DOI article.

    Tries fast requests-based fetch first; falls back to Playwright
    (headless browser) for JavaScript-rendered pages like React/MUI.
    """
    print(f"Fetching: {doi_url}")

    # --- Try requests first (fast) ---
    try:
        result = _extract_with_requests(doi_url)
        if result and result[1]:
            heading, content = result
            print("[requests] Found statement.")
            return {"doi_url": doi_url, "heading": heading, "content": content}
        elif result:
            print("[requests] Found heading but no content — trying Playwright...")
        else:
            print("[requests] Heading not found — trying Playwright...")
    except Exception as e:
        print(f"[requests] Error: {e} — trying Playwright...")

    # --- Fall back to Playwright (handles JS-rendered pages) ---
    try:
        result = _extract_with_playwright(doi_url)
        if result:
            heading, content = result
            if content:
                print("[playwright] Found statement.")
                return {"doi_url": doi_url, "heading": heading, "content": content}
            else:
                return {
                    "doi_url": doi_url,
                    "heading": heading,
                    "content": "Heading found but no content could be extracted.",
                }
        else:
            return {"doi_url": doi_url, "error": "Data availability statement not found on page."}
    except ImportError:
        return {
            "doi_url": doi_url,
            "error": (
                "Page requires JavaScript rendering but Playwright is not installed.\n"
                "Run:  pip install playwright && playwright install chromium"
            ),
        }
    except Exception as e:
        return {"doi_url": doi_url, "error": f"Playwright error: {e}"}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    doi_urls = [
        "http://dx.doi.org/10.12688/verixiv.403.2",
        # Add more DOI URLs here
    ]

    for url in doi_urls:
        print(f"\n{'='*60}")
        result = extract_data_availability_statement(url)
        print("=" * 60)

        if "error" in result:
            print(f"ERROR   : {result['error']}")
        else:
            print(f"Heading : {result['heading']}")
            print(f"\nContent :\n{result['content']}")


if __name__ == "__main__":
    main()

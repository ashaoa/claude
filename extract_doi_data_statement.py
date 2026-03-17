"""
Extract the Data Availability Statement from a DOI article URL.

Install dependencies (Replit Shell):
    pip install requests beautifulsoup4 selenium webdriver-manager
"""

import json
import re
import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Shared HTML parser
# ---------------------------------------------------------------------------

def _parse_html(html: str) -> tuple[str, str] | None:
    """Parse rendered HTML and return (heading_text, content) or None."""
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

    # Strategy A: collect sibling elements until the next heading
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

    # Strategy B: parent container text minus the heading
    parent = heading_tag.find_parent(["section", "article", "div"])
    if parent:
        content = parent.get_text(separator=" ", strip=True).replace(heading_text, "", 1).strip()
        if content:
            return heading_text, content

    return heading_text, ""


# ---------------------------------------------------------------------------
# Strategy 1: requests — plain HTML (fast, works for SSR pages)
# ---------------------------------------------------------------------------

def _fetch_html_requests(url: str) -> str:
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
    return resp.text


# ---------------------------------------------------------------------------
# Strategy 2: embedded JSON (Next.js / React apps store data in __NEXT_DATA__)
# ---------------------------------------------------------------------------

def _search_json(obj, keywords: list[str]) -> str | None:
    """Recursively search a JSON object for a string value matching keywords."""
    if isinstance(obj, str):
        low = obj.lower()
        if any(k in low for k in keywords) and len(obj) > 30:
            return obj
    elif isinstance(obj, dict):
        for v in obj.values():
            result = _search_json(v, keywords)
            if result:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = _search_json(item, keywords)
            if result:
                return result
    return None


def _extract_from_embedded_json(html: str) -> tuple[str, str] | None:
    """
    Look for data embedded in <script> tags (Next.js __NEXT_DATA__, etc.)
    and search for Data Availability Statement content.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Patterns to check: id="__NEXT_DATA__", type="application/json", or inline JSON vars
    script_tags = soup.find_all("script", {"id": "__NEXT_DATA__"})
    script_tags += soup.find_all("script", {"type": "application/json"})
    # Also check plain scripts containing large JSON blobs
    for s in soup.find_all("script"):
        text = s.string or ""
        if len(text) > 500 and ("dataAvailability" in text or "data_availability" in text
                                 or "DataAvailability" in text):
            script_tags.append(s)

    keywords = ["data availability", "data statement"]

    for script in script_tags:
        raw = script.string
        if not raw:
            continue
        # Strip leading variable assignment like: window.__X = {...}
        raw = re.sub(r"^[^{[]*", "", raw.strip())
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        content = _search_json(data, keywords)
        if content:
            # Strip HTML tags if the content is HTML
            clean = BeautifulSoup(content, "html.parser").get_text(separator=" ", strip=True)
            if clean:
                return "Data availability statement", clean

    return None


# ---------------------------------------------------------------------------
# Strategy 3: Selenium headless Chrome (handles JS-rendered pages on Replit)
# ---------------------------------------------------------------------------

def _fetch_html_selenium(url: str) -> str:
    from selenium import webdriver                              # noqa: PLC0415
    from selenium.webdriver.chrome.options import Options       # noqa: PLC0415
    from selenium.webdriver.chrome.service import Service       # noqa: PLC0415
    from selenium.webdriver.support.ui import WebDriverWait     # noqa: PLC0415
    from selenium.webdriver.support import expected_conditions as EC  # noqa: PLC0415
    from selenium.webdriver.common.by import By                 # noqa: PLC0415

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")

    # Try webdriver-manager first (auto-downloads matching ChromeDriver)
    try:
        from webdriver_manager.chrome import ChromeDriverManager  # noqa: PLC0415
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options,
        )
    except Exception:
        # Fall back to system chromedriver
        driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        # Wait up to 20s for an h2 or h3 to appear (page JS to finish)
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h2, h3"))
            )
        except Exception:
            pass
        return driver.page_source
    finally:
        driver.quit()


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def extract_data_availability_statement(doi_url: str) -> dict:
    """
    Extracts the Data Availability Statement from a DOI article.

    Order of attempts:
      1. requests + plain HTML parse
      2. requests + embedded JSON parse (Next.js __NEXT_DATA__ etc.)
      3. Selenium headless Chrome (full JS rendering)
    """
    print(f"Fetching: {doi_url}")

    # Step 1 & 2: requests (no browser needed)
    try:
        html = _fetch_html_requests(doi_url)

        result = _parse_html(html)
        if result and result[1]:
            print("[requests/html] Found statement.")
            return {"doi_url": doi_url, "heading": result[0], "content": result[1]}

        result = _extract_from_embedded_json(html)
        if result and result[1]:
            print("[requests/json] Found statement in embedded JSON.")
            return {"doi_url": doi_url, "heading": result[0], "content": result[1]}

        print("[requests] Not found in static HTML or embedded JSON — trying Selenium...")
    except Exception as e:
        print(f"[requests] Error: {e} — trying Selenium...")

    # Step 3: Selenium (full JS rendering)
    try:
        html = _fetch_html_selenium(doi_url)
        result = _parse_html(html)
        if result:
            heading, content = result
            print("[selenium] Found statement." if content else "[selenium] Heading found, no content.")
            return {
                "doi_url": doi_url,
                "heading": heading,
                "content": content or "Heading found but no content could be extracted.",
            }
        return {"doi_url": doi_url, "error": "Data availability statement not found on page."}
    except ImportError:
        return {
            "doi_url": doi_url,
            "error": "Selenium not installed. Run: pip install selenium webdriver-manager",
        }
    except Exception as e:
        return {"doi_url": doi_url, "error": f"Selenium error: {e}"}


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

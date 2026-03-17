"""
Extract specific sections (Funding, Acknowledgments, Conflicts of Interest)
from academic article URLs (e.g., MDPI, PMC, etc.)
"""

import re
import sys
import requests
from html.parser import HTMLParser


TARGET_SECTIONS = {"funding", "acknowledgments", "acknowledgements", "conflicts of interest"}


class SectionExtractor(HTMLParser):
    """
    Parses HTML and extracts text content for sections whose <h2> title
    matches one of the TARGET_SECTIONS.
    """

    def __init__(self):
        super().__init__()
        self.sections: dict[str, str] = {}
        self._current_section: str | None = None
        self._in_h2: bool = False
        self._h2_text: str = ""
        self._capture: bool = False
        self._depth: int = 0          # nesting depth while capturing
        self._buffer: list[str] = []  # collects text while capturing
        self._skip_tags: set[str] = {"script", "style", "noscript"}
        self._in_skip: int = 0        # depth counter for skipped tags

    # ------------------------------------------------------------------
    def handle_starttag(self, tag: str, attrs):
        if tag in self._skip_tags:
            self._in_skip += 1
            return

        if tag == "h2":
            # Finish any running capture before starting a new heading
            self._finish_section()
            self._in_h2 = True
            self._h2_text = ""
            return

        if self._capture:
            self._depth += 1

    def handle_endtag(self, tag: str):
        if tag in self._skip_tags:
            self._in_skip = max(0, self._in_skip - 1)
            return

        if tag == "h2":
            self._in_h2 = False
            heading = self._h2_text.strip().lower()
            if heading in TARGET_SECTIONS:
                self._current_section = self._h2_text.strip()
                self._capture = True
                self._depth = 0
                self._buffer = []
            return

        if self._capture:
            if self._depth > 0:
                self._depth -= 1
            else:
                # We've closed back to the level of the section container
                # Keep capturing — let the next h2 close the section
                pass

    def handle_data(self, data: str):
        if self._in_skip:
            return
        if self._in_h2:
            self._h2_text += data
        elif self._capture:
            self._buffer.append(data)

    # ------------------------------------------------------------------
    def _finish_section(self):
        if self._current_section and self._buffer:
            text = _clean(" ".join(self._buffer))
            if text:
                self.sections[self._current_section] = text
        self._current_section = None
        self._capture = False
        self._buffer = []
        self._depth = 0

    def close(self):
        self._finish_section()
        super().close()


# ---------------------------------------------------------------------------
def _clean(text: str) -> str:
    """Collapse whitespace and strip."""
    return re.sub(r"\s+", " ", text).strip()


def _make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    )
    return session


def extract_sections(url: str, timeout: int = 30) -> dict[str, str]:
    """
    Fetch *url* and return a dict mapping section headings to their text.

    Returns an empty dict if the page cannot be fetched or no target
    sections are found.
    """
    session = _make_session()
    try:
        resp = session.get(url, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"[ERROR] Could not fetch {url}: {exc}", file=sys.stderr)
        return {}

    parser = SectionExtractor()
    parser.feed(resp.text)
    parser.close()
    return parser.sections


def extract_sections_from_html(html: str) -> dict[str, str]:
    """Parse already-fetched HTML (useful for testing without network)."""
    parser = SectionExtractor()
    parser.feed(html)
    parser.close()
    return parser.sections


# ---------------------------------------------------------------------------
def print_sections(url: str, sections: dict[str, str]) -> None:
    print(f"\n{'=' * 70}")
    print(f"URL: {url}")
    print("=" * 70)
    if not sections:
        print("  No target sections found.")
        return
    for heading, content in sections.items():
        print(f"\n[{heading}]\n{content}\n")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    urls = sys.argv[1:] if len(sys.argv) > 1 else [
        "https://www.mdpi.com/2076-393X/13/10/1075",
    ]

    for url in urls:
        sections = extract_sections(url)
        print_sections(url, sections)

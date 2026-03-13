"""Fetch 'Sent for peer review' dates from eLife articles given DOIs."""

import re
import time
from html.parser import HTMLParser

import requests


DOIS = [
    "10.7554/elife.100268.3",
    "10.7554/elife.100478.3",
    "10.7554/elife.100822.3",
    "10.7554/elife.100840.3",
    "10.7554/elife.101011.3",
    "10.7554/elife.101841.3",
    "10.7554/elife.101924",
    "10.7554/elife.102324",
    "10.7554/elife.102515",
    "10.7554/elife.103403.3",
    "10.7554/elife.104008",
    "10.7554/elife.104045",
    "10.7554/elife.104237",
    "10.7554/elife.104237.3",
    "10.7554/elife.105978",
    "10.7554/elife.106075",
    "10.7554/elife.106537",
    "10.7554/elife.106537.2",
    "10.7554/elife.107114",
    "10.7554/elife.86931.3",
    "10.7554/elife.87018.5",
    "10.7554/elife.87930.3",
    "10.7554/elife.90269.3",
    "10.7554/elife.91582.3",
    "10.7554/elife.93033.4",
    "10.7554/elife.93621.4",
    "10.7554/elife.94420.3",
    "10.7554/elife.94982.4",
    "10.7554/elife.95125.3",
    "10.7554/elife.95135.3",
    "10.7554/elife.95243.3",
    "10.7554/elife.95823.4",
    "10.7554/elife.95842.3",
    "10.7554/elife.96724.3",
    "10.7554/elife.96803.4",
    "10.7554/elife.96839.3",
    "10.7554/elife.97098.3",
    "10.7554/elife.97179.3",
    "10.7554/elife.97313.3",
    "10.7554/elife.98009.4",
    "10.7554/elife.98114.4",
    "10.7554/elife.98158.4",
    "10.7554/elife.98257.4",
    "10.7554/elife.98522.3",
    "10.7554/elife.98622.3",
    "10.7554/elife.99373.3",
    "10.7554/elife.99752.4",
    "10.7554/elife.99785.3",
]

_DOI_RE = re.compile(
    r"10\.7554/elife\.(\d+)(?:\.(\d+))?$",
    re.IGNORECASE,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class _PeerReviewDateParser(HTMLParser):
    """Extracts the 'Sent for peer review' date from eLife article HTML.

    State machine:
      - Watches for ``<li>`` tags.
      - Inside an ``<li>``, collects text and looks for a ``<time>`` element.
      - Once ``<li>`` closes, checks if accumulated text contains the phrase
        and, if so, records the datetime value.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_li: bool = False
        self._li_text: list[str] = []
        self._time_datetime: str | None = None
        self._time_text: list[str] = []
        self._in_time: bool = False
        self.result: str | None = None

    # ------------------------------------------------------------------
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "li":
            self._in_li = True
            self._li_text = []
            self._time_datetime = None
            self._time_text = []
            self._in_time = False
        elif tag == "time" and self._in_li:
            self._in_time = True
            attr_dict = dict(attrs)
            self._time_datetime = attr_dict.get("datetime")
            self._time_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "time" and self._in_time:
            self._in_time = False
        elif tag == "li" and self._in_li:
            self._in_li = False
            combined = " ".join(self._li_text)
            if "Sent for peer review" in combined and self.result is None:
                if self._time_datetime:
                    self.result = self._time_datetime
                elif self._time_text:
                    self.result = "".join(self._time_text).strip()

    def handle_data(self, data: str) -> None:
        if self._in_time:
            self._time_text.append(data)
            if self._in_li:
                self._li_text.append(data)
        elif self._in_li:
            self._li_text.append(data)


def doi_to_url(doi: str) -> str:
    """Convert an eLife DOI to its article page URL.

    Examples
    --------
    >>> doi_to_url("10.7554/elife.100268.3")
    'https://elifesciences.org/articles/100268v3'
    >>> doi_to_url("10.7554/elife.101924")
    'https://elifesciences.org/articles/101924'
    """
    m = _DOI_RE.match(doi)
    if not m:
        raise ValueError(f"Unrecognised eLife DOI format: {doi!r}")
    article_id, version = m.group(1), m.group(2)
    if version:
        return f"https://elifesciences.org/articles/{article_id}v{version}"
    return f"https://elifesciences.org/articles/{article_id}"


def extract_peer_review_date(html: str) -> str | None:
    """Parse HTML and return the 'Sent for peer review' date string.

    The date is extracted from the ``datetime`` attribute of the ``<time>``
    element inside the ``<li>Sent for peer review: …</li>`` list item.
    Falls back to the visible text content of the ``<time>`` element when the
    attribute is absent.

    Returns ``None`` if the element is not found.
    """
    parser = _PeerReviewDateParser()
    parser.feed(html)
    return parser.result


def fetch_peer_review_date(
    doi: str,
    session: requests.Session,
    delay: float = 1.0,
) -> str | None:
    """Fetch the eLife article page and return the peer-review date string.

    Parameters
    ----------
    doi:
        An eLife DOI such as ``"10.7554/elife.100268.3"``.
    session:
        A :class:`requests.Session` used for the HTTP request.
    delay:
        Seconds to sleep *after* the request (polite crawling).

    Returns
    -------
    str or None
        The date string from the ``<time datetime="…">`` element, or ``None``
        if the page could not be fetched or the element was not found.
    """
    url = doi_to_url(doi)
    try:
        resp = session.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"  ERROR fetching {url}: {exc}")
        return None
    finally:
        time.sleep(delay)
    return extract_peer_review_date(resp.text)


def fetch_all(
    dois: list[str] | None = None,
    delay: float = 1.0,
) -> dict[str, str | None]:
    """Return a mapping of DOI -> peer-review date for every supplied DOI.

    Parameters
    ----------
    dois:
        List of DOIs to process.  Defaults to the module-level :data:`DOIS`.
    delay:
        Polite delay in seconds between requests.
    """
    if dois is None:
        dois = DOIS
    results: dict[str, str | None] = {}
    with requests.Session() as session:
        for doi in dois:
            print(f"Fetching {doi} …")
            results[doi] = fetch_peer_review_date(doi, session, delay=delay)
            print(f"  -> {results[doi]}")
    return results


if __name__ == "__main__":
    results = fetch_all()
    print("\n=== Results ===")
    for doi, peer_date in results.items():
        print(f"{doi}: {peer_date}")

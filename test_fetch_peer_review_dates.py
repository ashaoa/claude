"""Tests for fetch_peer_review_dates module."""

import unittest
from unittest.mock import MagicMock, patch  # noqa: F401 – MagicMock used in helpers

from fetch_peer_review_dates import (
    doi_to_url,
    extract_peer_review_date,
    fetch_peer_review_date,
)


class TestDoiToUrl(unittest.TestCase):
    def test_versioned_doi(self):
        self.assertEqual(
            doi_to_url("10.7554/elife.100268.3"),
            "https://elifesciences.org/articles/100268v3",
        )

    def test_versioned_doi_v5(self):
        self.assertEqual(
            doi_to_url("10.7554/elife.87018.5"),
            "https://elifesciences.org/articles/87018v5",
        )

    def test_unversioned_doi(self):
        self.assertEqual(
            doi_to_url("10.7554/elife.101924"),
            "https://elifesciences.org/articles/101924",
        )

    def test_invalid_doi_raises(self):
        with self.assertRaises(ValueError):
            doi_to_url("10.1234/other.12345")

    def test_case_insensitive(self):
        self.assertEqual(
            doi_to_url("10.7554/eLife.100268.3"),
            "https://elifesciences.org/articles/100268v3",
        )


class TestExtractPeerReviewDate(unittest.TestCase):
    _HTML_WITH_DATE = (
        "<html><body><ul>"
        '<li>Received: <time datetime="January 1, 2024">January 1, 2024</time></li>'
        '<li>Sent for peer review: <time datetime="June 11, 2024">June 11, 2024</time></li>'
        '<li>Published: <time datetime="July 1, 2024">July 1, 2024</time></li>'
        "</ul></body></html>"
    )

    _HTML_WITH_ISO_DATE = (
        "<html><body><ul>"
        '<li>Sent for peer review: <time datetime="2024-06-11">June 11, 2024</time></li>'
        "</ul></body></html>"
    )

    _HTML_WITHOUT_DATETIME_ATTR = (
        "<html><body><ul>"
        "<li>Sent for peer review: <time>March 5, 2024</time></li>"
        "</ul></body></html>"
    )

    _HTML_NO_PEER_REVIEW = (
        "<html><body><ul>"
        '<li>Received: <time datetime="January 1, 2024">January 1, 2024</time></li>'
        "</ul></body></html>"
    )

    def test_extracts_datetime_attribute(self):
        self.assertEqual(extract_peer_review_date(self._HTML_WITH_DATE), "June 11, 2024")

    def test_extracts_iso_datetime_attribute(self):
        self.assertEqual(extract_peer_review_date(self._HTML_WITH_ISO_DATE), "2024-06-11")

    def test_falls_back_to_text_when_no_attribute(self):
        self.assertEqual(
            extract_peer_review_date(self._HTML_WITHOUT_DATETIME_ATTR), "March 5, 2024"
        )

    def test_returns_none_when_not_found(self):
        self.assertIsNone(extract_peer_review_date(self._HTML_NO_PEER_REVIEW))

    def test_empty_html(self):
        self.assertIsNone(extract_peer_review_date(""))

    def test_first_match_wins(self):
        html = (
            "<ul>"
            '<li>Sent for peer review: <time datetime="April 1, 2024">April 1, 2024</time></li>'
            '<li>Sent for peer review: <time datetime="May 1, 2024">May 1, 2024</time></li>'
            "</ul>"
        )
        self.assertEqual(extract_peer_review_date(html), "April 1, 2024")


class TestFetchPeerReviewDate(unittest.TestCase):
    _SAMPLE_HTML = (
        "<html><body><ul>"
        '<li>Sent for peer review: <time datetime="June 11, 2024">June 11, 2024</time></li>'
        "</ul></body></html>"
    )

    def _make_urlopen(self, html: str):
        """Return a context-manager mock that yields a response with read()."""
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=cm)
        cm.__exit__ = MagicMock(return_value=False)
        cm.read.return_value = html.encode("utf-8")
        return cm

    @patch("fetch_peer_review_dates.time.sleep")
    @patch("fetch_peer_review_dates.urllib.request.urlopen")
    def test_returns_date_on_success(self, mock_urlopen, _mock_sleep):
        mock_urlopen.return_value = self._make_urlopen(self._SAMPLE_HTML)
        result = fetch_peer_review_date("10.7554/elife.100268.3", delay=0)
        self.assertEqual(result, "June 11, 2024")

    @patch("fetch_peer_review_dates.time.sleep")
    @patch("fetch_peer_review_dates.urllib.request.urlopen")
    def test_returns_none_on_http_error(self, mock_urlopen, _mock_sleep):
        import urllib.error as _ue

        mock_urlopen.side_effect = _ue.URLError("connection error")
        result = fetch_peer_review_date("10.7554/elife.100268.3", delay=0)
        self.assertIsNone(result)

    @patch("fetch_peer_review_dates.time.sleep")
    @patch("fetch_peer_review_dates.urllib.request.urlopen")
    def test_sleeps_after_request(self, mock_urlopen, mock_sleep):
        mock_urlopen.return_value = self._make_urlopen(self._SAMPLE_HTML)
        fetch_peer_review_date("10.7554/elife.100268.3", delay=1.5)
        mock_sleep.assert_called_once_with(1.5)


if __name__ == "__main__":
    unittest.main()

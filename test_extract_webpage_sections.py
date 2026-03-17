"""Tests for extract_webpage_sections.py"""

import unittest
from unittest.mock import patch, MagicMock
from extract_webpage_sections import extract_sections, extract_sections_from_html


# ---------------------------------------------------------------------------
# Sample HTML that mimics MDPI article structure
SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test Article</title></head>
<body>
  <h2>Abstract</h2>
  <p>This paper investigates vaccine efficacy...</p>

  <h2>Introduction</h2>
  <p>Vaccines are critical for public health...</p>

  <h2>Funding</h2>
  <p>This research was funded by the National Institutes of Health,
  grant number R01-AI-12345, and by the European Research Council
  under grant agreement No 987654.</p>

  <h2>Acknowledgments</h2>
  <p>The authors thank Dr. Jane Smith for providing the cell lines
  and Prof. John Doe for critical reading of the manuscript.</p>

  <h2>Conflicts of Interest</h2>
  <p>The authors declare no conflict of interest. The funders had no
  role in the design of the study.</p>

  <h2>References</h2>
  <p>1. Smith J, et al. ...</p>
</body>
</html>
"""

# HTML where section uses "Acknowledgements" (British spelling)
SAMPLE_HTML_ALT_SPELLING = """
<html><body>
  <h2>Acknowledgements</h2>
  <p>We thank our collaborators at University X.</p>
  <h2>Funding</h2>
  <p>Funded by Grant ABC-123.</p>
  <h2>Next Section</h2>
</body></html>
"""

# HTML with no target sections
SAMPLE_HTML_NO_SECTIONS = """
<html><body>
  <h2>Introduction</h2><p>Some intro text.</p>
  <h2>Methods</h2><p>Methods described here.</p>
</body></html>
"""

# HTML with inline script/style noise inside a section
SAMPLE_HTML_WITH_NOISE = """
<html><body>
  <h2>Funding</h2>
  <div>
    <p>Funded by Agency X.</p>
    <script>alert('noise')</script>
    <style>.x{color:red}</style>
    <p>Additional funding from Agency Y.</p>
  </div>
  <h2>Next</h2>
</body></html>
"""


class TestExtractSectionsFromHtml(unittest.TestCase):

    def test_all_three_sections_present(self):
        result = extract_sections_from_html(SAMPLE_HTML)
        self.assertIn("Funding", result)
        self.assertIn("Acknowledgments", result)
        self.assertIn("Conflicts of Interest", result)

    def test_funding_content(self):
        result = extract_sections_from_html(SAMPLE_HTML)
        self.assertIn("National Institutes of Health", result["Funding"])
        self.assertIn("R01-AI-12345", result["Funding"])

    def test_acknowledgments_content(self):
        result = extract_sections_from_html(SAMPLE_HTML)
        self.assertIn("Jane Smith", result["Acknowledgments"])

    def test_conflicts_content(self):
        result = extract_sections_from_html(SAMPLE_HTML)
        self.assertIn("no conflict of interest", result["Conflicts of Interest"])

    def test_non_target_sections_excluded(self):
        result = extract_sections_from_html(SAMPLE_HTML)
        self.assertNotIn("Abstract", result)
        self.assertNotIn("Introduction", result)
        self.assertNotIn("References", result)

    def test_alternative_acknowledgements_spelling(self):
        result = extract_sections_from_html(SAMPLE_HTML_ALT_SPELLING)
        # Either spelling should be captured
        found = any("Acknowledg" in k for k in result)
        self.assertTrue(found, f"Acknowledgements not found in {list(result.keys())}")

    def test_no_target_sections(self):
        result = extract_sections_from_html(SAMPLE_HTML_NO_SECTIONS)
        self.assertEqual(result, {})

    def test_script_style_noise_excluded(self):
        result = extract_sections_from_html(SAMPLE_HTML_WITH_NOISE)
        self.assertIn("Funding", result)
        self.assertNotIn("alert", result["Funding"])
        self.assertNotIn("color:red", result["Funding"])
        self.assertIn("Agency X", result["Funding"])
        self.assertIn("Agency Y", result["Funding"])

    def test_empty_html(self):
        result = extract_sections_from_html("")
        self.assertEqual(result, {})

    def test_whitespace_collapsed(self):
        html = "<html><body><h2>Funding</h2><p>  A   B   C  </p><h2>X</h2></body></html>"
        result = extract_sections_from_html(html)
        self.assertEqual(result["Funding"], "A B C")


class TestExtractSectionsNetwork(unittest.TestCase):
    """Tests that mock the network layer."""

    def _mock_response(self, html: str, status: int = 200):
        resp = MagicMock()
        resp.status_code = status
        resp.text = html
        resp.raise_for_status = MagicMock()
        return resp

    @patch("extract_webpage_sections.requests.Session")
    def test_successful_fetch(self, MockSession):
        MockSession.return_value.get.return_value = self._mock_response(SAMPLE_HTML)
        MockSession.return_value.headers = {}
        result = extract_sections("https://example.com/article")
        self.assertIn("Funding", result)
        self.assertIn("Acknowledgments", result)
        self.assertIn("Conflicts of Interest", result)

    @patch("extract_webpage_sections.requests.Session")
    def test_http_error_returns_empty(self, MockSession):
        import requests as req
        mock_resp = self._mock_response("", 403)
        mock_resp.raise_for_status.side_effect = req.HTTPError("403")
        MockSession.return_value.get.return_value = mock_resp
        MockSession.return_value.headers = {}
        result = extract_sections("https://example.com/blocked")
        self.assertEqual(result, {})

    @patch("extract_webpage_sections.requests.Session")
    def test_connection_error_returns_empty(self, MockSession):
        import requests as req
        MockSession.return_value.get.side_effect = req.ConnectionError("timeout")
        MockSession.return_value.headers = {}
        result = extract_sections("https://example.com/unreachable")
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main(verbosity=2)

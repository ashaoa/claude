import requests
from bs4 import BeautifulSoup


def extract_data_availability_statement(doi_url: str) -> dict:
    """
    Extracts the Data Availability Statement section from a DOI article URL.

    Args:
        doi_url: A DOI URL (e.g., http://dx.doi.org/10.12688/verixiv.403.2)

    Returns:
        A dict with 'heading' and 'content' keys, or an error message.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    # Follow DOI redirect to actual article page
    response = requests.get(doi_url, headers=headers, allow_redirects=True, timeout=30)
    response.raise_for_status()

    final_url = response.url
    print(f"Resolved URL: {final_url}")

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the Data Availability Statement heading (h2 with matching text)
    heading_tag = None
    for tag in soup.find_all(["h2", "h3"]):
        text = tag.get_text(strip=True).lower()
        if "data availability" in text or "data statement" in text:
            heading_tag = tag
            break

    if not heading_tag:
        return {"error": "Data availability statement section not found on page."}

    heading_text = heading_tag.get_text(strip=True)

    # Collect all content after the heading until the next heading of same/higher level
    content_parts = []
    tag_level = int(heading_tag.name[1])  # e.g. h2 -> 2

    for sibling in heading_tag.find_next_siblings():
        sibling_name = sibling.name
        # Stop if we hit the next heading of same or higher level
        if sibling_name in ["h1", "h2", "h3", "h4"] and int(sibling_name[1]) <= tag_level:
            break
        text = sibling.get_text(separator=" ", strip=True)
        if text:
            content_parts.append(text)

    content = "\n".join(content_parts).strip()

    # Fallback: try the parent section/article container
    if not content:
        parent = heading_tag.find_parent(["section", "article", "div"])
        if parent:
            content = parent.get_text(separator=" ", strip=True)

    return {
        "doi_url": doi_url,
        "resolved_url": final_url,
        "heading": heading_text,
        "content": content if content else "No content found after heading.",
    }


def main():
    doi_urls = [
        "http://dx.doi.org/10.12688/verixiv.403.2",
    ]

    for url in doi_urls:
        print(f"\n{'='*60}")
        print(f"Processing: {url}")
        print("=" * 60)

        result = extract_data_availability_statement(url)

        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Heading : {result['heading']}")
            print(f"Content :\n{result['content']}")


if __name__ == "__main__":
    main()

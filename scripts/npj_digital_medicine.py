import os
import time
from urllib.parse import urljoin, urlparse

import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup

# Index for npj Digital Medicine research articles in 2025
BASE_INDEX_URL = (
    "https://www.nature.com/npjdigitalmed/research-articles"
    "?type=article&year=2025&searchType=journalSearch&sort=PubDate"
)
BASE_DOMAIN = "https://www.nature.com"
OUT_DIR = "npjdigitalmed_2025_pdfs"

# Be polite
REQUEST_DELAY = 1.0  # seconds between requests
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; NPJDigitalMedDownloader/1.0; "
        "+https://example.org/)"
    )
}


def fetch(url, allow_404=False):
    """GET wrapper with basic error handling and a short delay."""
    time.sleep(REQUEST_DELAY)
    resp = requests.get(url, headers=HEADERS)

    if allow_404:
        # If the caller is prepared to handle missing pages, just return None
        if resp.status_code == 404:
            print(f"[index] Got 404 for {url}")
            return None
        # For other errors, still raise
        try:
            resp.raise_for_status()
        except HTTPError as e:
            print(f"[error] HTTP error for {url}: {e}")
            raise
        return resp

    # Default behaviour: raise on any error
    resp.raise_for_status()
    return resp


def find_article_links_in_index(html):
    """
    Parse an index page and return a set of article URLs.

    Strategy:
    - Find all <h3> tags.
    - For each <h3>, look for a child <a href="/articles/...">.
    - Build full URLs and deduplicate.
    """
    soup = BeautifulSoup(html, "html.parser")
    article_urls = set()

    for h3 in soup.find_all("h3"):
        a = h3.find("a", href=True)
        if not a:
            continue
        href = a["href"]
        # npj Digital Medicine research articles are under /articles/<something>
        if "/articles/" in href:
            full = urljoin(BASE_DOMAIN, href)
            article_urls.add(full)

    return article_urls


def iter_index_pages():
    """
    Generator that yields article URLs from each index page.

    We keep increasing `page` until either:
    - We get a 404 (no such page), or
    - The page has no article links.
    """
    page = 1

    while True:
        if page == 1:
            url = BASE_INDEX_URL
        else:
            url = BASE_INDEX_URL + f"&page={page}"

        print(f"[index] Fetching page {page}: {url}")
        resp = fetch(url, allow_404=True)
        if resp is None:
            print(f"[index] Page {page} returned 404; assuming no more pages.")
            break

        article_urls = find_article_links_in_index(resp.text)
        if not article_urls:
            print(f"[index] No articles found on page {page}, stopping.")
            break

        # Yield the URLs from this page, then move to next
        for a in article_urls:
            yield a

        page += 1


def get_pdf_url_from_article(html, article_url):
    """
    Given article HTML, try to extract a PDF URL.

    1. Look for an <a> tag whose text includes 'Download PDF'.
    2. Fallback: <meta name="citation_pdf_url" content="...">
    """
    soup = BeautifulSoup(html, "html.parser")

    # 1) Look for the 'Download PDF' button/link
    link = soup.find("a", string=lambda s: s and "Download PDF" in s)
    if link and link.get("href"):
        pdf_url = urljoin(BASE_DOMAIN, link["href"])
        return pdf_url

    # 2) Fallback to meta tag
    meta = soup.find("meta", attrs={"name": "citation_pdf_url"})
    if meta and meta.get("content"):
        return meta["content"]

    # Nothing found
    print(f"[warn] No PDF link found for article: {article_url}")
    return None


def derive_filename_from_article_url(article_url):
    """
    Derive a reasonable filename from the article URL.

    Example:
        https://www.nature.com/articles/s41746-025-00001-x
        -> s41746-025-00001-x.pdf
    """
    path = urlparse(article_url).path  # e.g. "/articles/s41746-025-00001-x"
    name = path.strip("/").split("/")[-1]  # last path component
    if not name:
        name = "article"
    return f"{name}.pdf"


def download_pdf(pdf_url, out_path):
    """Download a single PDF to out_path."""
    if os.path.exists(out_path):
        print(f"[skip] Already exists: {out_path}")
        return

    print(f"[pdf] Downloading {pdf_url} -> {out_path}")
    resp = fetch(pdf_url)

    # crude content-type sanity check
    ctype = resp.headers.get("Content-Type", "")
    if "pdf" not in ctype.lower():
        print(f"[warn] Content-type not PDF ({ctype}) for {pdf_url}, saving anyway.")

    with open(out_path, "wb") as f:
        f.write(resp.content)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # Collect all article URLs (deduplicated)
    all_articles = set(iter_index_pages())
    print(f"[info] Found {len(all_articles)} article URLs in 2025 index for npj Digital Medicine.")

    for i, article_url in enumerate(sorted(all_articles), start=1):
        print(f"\n[article {i}/{len(all_articles)}] {article_url}")
        try:
            article_resp = fetch(article_url)
        except Exception as e:
            print(f"[error] Failed to fetch article page: {e}")
            continue

        pdf_url = get_pdf_url_from_article(article_resp.text, article_url)
        if not pdf_url:
            continue

        filename = derive_filename_from_article_url(article_url)
        out_path = os.path.join(OUT_DIR, filename)

        try:
            download_pdf(pdf_url, out_path)
        except Exception as e:
            print(f"[error] Failed to download PDF {pdf_url}: {e}")


if __name__ == "__main__":
    main()

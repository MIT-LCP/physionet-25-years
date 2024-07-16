"""
Download NeurIPS papers and create a summary spreadsheet.
"""

import requests
from bs4 import BeautifulSoup
import csv
import os


def fetch_page_content(url):
    """
    Fetch the page content
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {str(e)}")
        return None


def load_existing_titles(csv_path):
    """
    Load a list of papers that have already been downloaded.
    """
    titles = set()
    try:
        with open(csv_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            # Skip header row
            next(reader)
            for row in reader:
                # Title is the first column
                titles.add(row[0])
    except FileNotFoundError:
        print("CSV file not found. Assuming no data has been processed.")
    return titles


def scrape_paper_details(url, csv_path):
    """
    Extract the title, authors, and links.
    """
    existing_titles = load_existing_titles(csv_path)
    html_content = fetch_page_content(url)
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    papers = soup.find_all('li', class_='conference')

    with open(csv_path, mode='a', newline='', encoding='utf-8') as file:  # Change to 'a' for appending
        writer = csv.writer(file)
        if os.stat(csv_path).st_size == 0:  # Write header if file is empty
            writer.writerow(['Title', 'Authors', 'Link', 'PDF Link'])

        for paper in papers:
            title = paper.find('a').text
            if title not in existing_titles:
                href = paper.find('a')['href']
                link = f'https://papers.nips.cc{href}'
                authors = paper.find('i').text if paper.find('i') else "No authors listed"
                pdf_link = fetch_pdf_link(link)

                writer.writerow([title, authors, link, pdf_link])

                if pdf_link != "PDF link not found":
                    download_pdf(pdf_link, title)
                existing_titles.add(title)  # Add title to set after processing


def fetch_pdf_link(paper_page_url):
    """
    Fetch the link to the PDF.
    """
    html_content = fetch_page_content(paper_page_url)
    if not html_content:
        return "PDF link not found"

    soup = BeautifulSoup(html_content, 'html.parser')
    pdf_link_element = soup.find('a', class_='btn btn-primary btn-spacer')
    if pdf_link_element and 'href' in pdf_link_element.attrs:
        pdf_url = f"https://papers.nips.cc{pdf_link_element['href']}"
        return pdf_url
    return "PDF link not found"


def download_pdf(pdf_url, title):
    """
    Download the PDF.
    """
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()
        if not os.path.exists('pdfs'):
            os.makedirs('pdfs')
        file_path = os.path.join('pdfs', f"{title}.pdf".replace('/', '_').replace('\\', '_').replace(':', '_'))
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {title}")
    except requests.RequestException as e:
        print(f"Failed to download PDF {pdf_url}: {str(e)}")

main_url = 'https://papers.nips.cc/paper_files/paper/2023'
csv_path = 'papers_metadata.csv'

# Check and create CSV if doesn't exist to handle header correctly
if not os.path.exists(csv_path):
    with open(csv_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Title', 'Authors', 'Link', 'PDF Link'])

# Scrape all paper details and save to CSV, download PDFs
scrape_paper_details(main_url, csv_path)

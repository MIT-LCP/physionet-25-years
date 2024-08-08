"""
models.py

This module contains data structures that represent conferences, journals, etc.

For example:
`Publication` Class: Represents an individual paper.
`PublicationVenue` Class: Represents either a conference or a journal.
`VenueCollection` Class: Represents a collection of publication venues.
"""
import os

import pymupdf


class PublicationVenue:
    """
    A class to represent a publication venue (either a conference or journal).

    Attributes:
    title (str): Full title of the venue.
    shortname (str): Abbreviated name of the venue.
    year (int): Year the venue was held or published.
    publications (list of Publication): List of publications.
    """

    def __init__(self, title, shortname, year, path, publications=None):
        """
        Constructs all the necessary attributes for the publication venue.

        Parameters:
        title (str): Full title of the venue.
        shortname (str): Abbreviated name of the venue.
        year (int): Year held or published.
        path (str): Path to folder containing publications.
        publications (list of Publication, optional): List of publications.
        """
        self.title = title
        self.shortname = shortname
        self.year = year
        self.path = path
        self.publications = publications if publications is not None else []

    def add_publication(self, publication):
        """
        Adds a publication to the list of publications associated with
        the venue.

        Parameters:
        publication (Publication): The publication to add to the venue.
        """
        self.publications.append(publication)

    def search_keywords(self, keywords):
        """
        Searches all publications in the venue for a set of keywords
        and records the findings.

        Parameters:
        keywords (list of str): A list of keywords to search for in
                                the publications.
        """
        for publication in self.publications:
            publication.find_keywords(keywords)

    def summarize(self):
        """
        Summarizes the proportion of publications containing the keywords.

        Parameters:
        keywords (list of str): List of keywords of interest.

        Returns:
        dict: Summary of the proportion of publications containing a keyword.
        """
        total_publications = len(self.publications)

        count = 0
        for publication in self.publications:
            if publication.includes_keyword:
                count += 1

        proportion_summary = {
            'total_publications': total_publications,
            'publications_containing_keyword': count,
            'proportion': count / total_publications * 100 if total_publications > 0 else 0
        }

        # Print the summary
        print(f"{self.title} ({self.year}):")
        print(f"- Total publications: {proportion_summary['total_publications']}")
        print(f"- Publications containing keyword: {proportion_summary['publications_containing_keyword']}")
        print(f"- Proportion of publications containing keyword: {proportion_summary['proportion']:.2f}%")
        print()

        return proportion_summary

    def __repr__(self):
        """
        Returns a string representation of the PublicationVenue object.
        """
        return (
            f"PublicationVenue(\n"
            f"  title={self.title!r},\n"
            f"  shortname={self.shortname!r},\n"
            f"  year={self.year},\n"
            f"  publications={self.publications}\n"
            f")"
        )


class Publication:
    """
    A class to represent a paper.

    Attributes:
    title (str): Title of the paper.
    authors (list of str): Authors of the paper.
    abstract (str): Abstract of the paper.
    pdf_path (str): Path to the PDF of the paper.
    """

    def __init__(self, path, filename, title=None, authors=None,
                 abstract=None):
        """
        Constructs all the necessary attributes for the paper object.

        Parameters:
        path (str): Path to the folder containing the paper.
        filename (str): Filename of the paper.
        title (str): Title of the paper.
        authors (list of str): Authors of the paper.
        abstract (str): Abstract of the paper.
        """
        self.path = path
        self.filename = filename
        self.title = title or "Unknown"
        self.authors = authors or "Unknown"
        self.abstract = abstract or "Unknown"
        self.includes_keyword = None
        self.keyword_passages = None

    def find_keywords(self, keywords):
        """
        Search the text for the keywords.

        Returns:
        - mentions_any (bool): True if a keyword is found, False if not.
        - passages (list): list of strings containing the keywords.
        """
        passages = []

        try:
            file = os.path.join(self.path, self.filename)
            doc = pymupdf.open(file)

            mentions_any = False

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()

                for keyword in keywords:
                    if keyword in text:
                        mentions_any = True
                        start_idx = text.find(keyword)

                        # Extract 100 characters around the keyword
                        start_passage = max(0, start_idx - 50)
                        end_passage = min(len(text), start_idx + 50)
                        passages.append(text[start_passage:end_passage])

            doc.close()
            self.includes_keyword = mentions_any
            self.keyword_passages = passages
        except pymupdf.FileDataError as e:
            print(f"Error reading PDF file: {e}")

    def __repr__(self):
        """
        Returns a string representation of the Paper object.
        """
        return f"Publication(title={self.filename!r}"


class VenueCollection:
    """
    A class to manage a collection of publication venues.

    Attributes:
    venues (list of PublicationVenue): List of publication venues.
    """

    def __init__(self):
        """
        Constructs an empty VenueCollection object.
        """
        self.venues = []

    def add(self, venue):
        """
        Adds a publication venue to the collection.

        Parameters:
        venue (PublicationVenue): The venue to add.
        """
        self.venues.append(venue)

    def get_venue_by_shortname(self, shortname):
        """
        Retrieves a publication venue by its shortname.

        Parameters:
        shortname (str): The shortname of the venue to retrieve.

        Returns:
        PublicationVenue: Venue object with the matching shortname, or None.
        """
        for venue in self.venues:
            if venue.shortname == shortname:
                return venue
        return None

    def get_venues_by_year(self, year):
        """
        Retrieves all publication venues held or published in a specific year.

        Parameters:
        year (int): Year filter.

        Returns:
        list of PublicationVenue: List of venues held in the specified year.
        """
        return [venue for venue in self.venues if venue.year == year]

    def search_keywords_across_venues(self, keywords):
        """
        Searches for keywords across all venues in the collection and
        records the findings.

        Parameters:
        keywords (list of str): List of keywords to search for in the
                                publications.
        """
        for venue in self.venues:
            venue.search_keywords(keywords)

    def __iter__(self):
        """
        Returns an iterator for the collection of publication venues.
        """
        return iter(self.venues)

    def __getitem__(self, index):
        """
        Returns the conference or journal at the specified index.

        Parameters:
        index (int): Index of the venue to retrieve.

        Returns:
        PublicationVenue: Conference or journal at the specified index.
        """
        return self.venues[index]

    def __len__(self):
        """
        Returns the number of conferences or journals in the collection.

        Returns:
        int: Number of conferences or journals.
        """
        return len(self.venues)

    def __repr__(self):
        """
        Returns a string representation of the VenueCollection object.
        """
        return (
            f"VenueCollection(\n"
            f"  venues={self.venues}\n"
            f")"
        )

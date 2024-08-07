# PhysioNet Quarter Century

Code for 25 years paper

## Installation

### 1. Install the `twentyfiveyears` package

Before running scripts in the `/scripts/` folder, you should install the `twentyfiveyears` package with:

```
pip install -e .
```

Scripts can then be run with:

```
python scripts/yourscript.py
```

## Links

Paper: https://docs.google.com/document/d/1eDlbaOF7ObhNyJ6hBzf-rLXCwViLRHXenTXN5Z2qfSU/edit#heading=h.eozrij9p5azs

Spreadsheet: https://docs.google.com/spreadsheets/d/1DuK7svMZ6U52PuqdxBkuCq60PQUmwnS6Vko-uMXcgPE/edit

PDFs: https://www.dropbox.com/scl/fo/a6ua6gn1ntbjjlpsrmes5/APAx0Dtqf4Ktz8d7CQoq7xo?rlkey=kwzm0l6zsq2wseb13v41hnmtz&dl=0

## Parse PDFs (`parse_pdfs.py`)

`parse_pdfs.py` is a script that will parse a folder containing PDFs and record whether or not a set of *case-sensitive* target words (MIMIC, PhysioNet, etc) are mentioned. The script is run with:

```
python parse_pdfs.py /path/to/pdfs keyword1 keyword2 keyword3 /path/to/output.csv
```

e.g.

```
python scripts/parse_pdfs.py ./papers/chil_2023/pdfs_subset/ PhysioNet physionet MIMIC-III WFDB ./output.csv
```

The script outputs a CSV containing the following three columns: 

- `Filename`: Filename of the PDF
- `Contains target word`: Yes/No flag indicating whether a target word (e.g. "PhysioNet") was found in the PDF.
- `Extracted text`: A passage (or list of passages) of text containing the target word.

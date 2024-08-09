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

### 2. Symlink the `data` folder to Dropbox

Data for this project is on Dropbox at:
https://www.dropbox.com/scl/fo/a6ua6gn1ntbjjlpsrmes5/APAx0Dtqf4Ktz8d7CQoq7xo?rlkey=kwzm0l6zsq2wseb13v41hnmtz&dl=0

You should symlink the Dropbox folder to a folder called `./data`. From the root of the cloned repository, do:

```
ln -s /path/to/dropbox/ data
```

This will create a new `data` folder containing papers, NIH reporter information, etc.

## Links

Spreadsheet: https://docs.google.com/spreadsheets/d/1DuK7svMZ6U52PuqdxBkuCq60PQUmwnS6Vko-uMXcgPE/edit

Data: https://www.dropbox.com/scl/fo/a6ua6gn1ntbjjlpsrmes5/APAx0Dtqf4Ktz8d7CQoq7xo?rlkey=kwzm0l6zsq2wseb13v41hnmtz&dl=0

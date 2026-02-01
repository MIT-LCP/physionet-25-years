# PhysioNet Quarter Century

## Plot figures

### 1. Prepare data

- Export user and publication data from PhysioNet.
- Export citation data from Dimensions: https://www.dimensions.ai/ 
- Copy data to the `data` folder

### 2. Run notebooks

Plot figures using the Python Notbooks:

- https://github.com/MIT-LCP/physionet-25-years/blob/main/notebooks/figure_1_timeline.ipynb
- https://github.com/MIT-LCP/physionet-25-years/blob/main/notebooks/figure_2_projects.ipynb
- https://github.com/MIT-LCP/physionet-25-years/blob/main/notebooks/figure_3_worldmap.ipynb
- https://github.com/MIT-LCP/physionet-25-years/blob/main/notebooks/figure_4_users.ipynb
- https://github.com/MIT-LCP/physionet-25-years/blob/main/notebooks/figure_5_citations.ipynb

## 1. `twentyfiveyears` package

Some code in this repository (for example, scripts in the `/scripts/` folder), require the `twentyfiveyears` package to be installed.

Install it with:

```
pip install -e .
```

Scripts can then be run with:

```
python scripts/yourscript.py
```

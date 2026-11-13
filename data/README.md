# Data

MAKOS uses only real, public datasets. Large or licence-restricted files are
downloaded by script and are never committed (see `.gitignore`).

## Stage 1: BPI Challenge 2019

Real purchase-to-pay event log of a multinational paints and coatings company
(60 subsidiaries, mostly 2018). Licence: CC BY 4.0.

Cite: van Dongen, B.F. (2019). *BPI Challenge 2019*. 4TU.ResearchData.
https://doi.org/10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1

Any OS (Windows, macOS, Linux):

```bash
python -m pip install -r requirements.txt
python data/scripts/download_bpi2019.py   # ~695 MB into data/raw/, writes CHECKSUMS.txt
python data/scripts/profile_bpi2019.py    # writes data/profile/bpi2019_profile.md
```

On macOS/Linux, `make install && make data && make profile` does the same.

If the download keeps failing, open
https://figshare.com/articles/dataset/BPI_Challenge_2019/12715853 in a browser,
click **Download**, put `BPI_Challenge_2019.xes` in `data/raw/`, then run the
download script once more: it sees the complete file and only writes the checksum.

`make profile` checks its counts against the published figures
(251,734 cases, 76,349 purchase documents, 1,595,923 events, 42 activities)
and exits with an error if they differ.

Commit `data/profile/` and `data/raw/CHECKSUMS.txt` after running it.

| Folder | Contents | In git? |
| --- | --- | --- |
| `raw/` | Downloaded source files | Only `CHECKSUMS.txt` |
| `interim/` | Parquet tables built from raw files | No |
| `profile/` | Profiling reports | Yes |
| `scripts/` | Download and processing code | Yes |

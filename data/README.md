# Data

MAKOS uses only real, public datasets. Large or licence-restricted files are
downloaded by script and are never committed (see `.gitignore`).

## Stage 1: BPI Challenge 2019

Real purchase-to-pay event log of a multinational paints and coatings company
(60 subsidiaries, mostly 2018). Licence: CC BY 4.0.

Cite: van Dongen, B.F. (2019). *BPI Challenge 2019*. 4TU.ResearchData.
https://doi.org/10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1

```bash
make install
make data      # downloads ~695 MB into data/raw/ and writes CHECKSUMS.txt
make profile   # converts to parquet and writes data/profile/bpi2019_profile.md
```

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

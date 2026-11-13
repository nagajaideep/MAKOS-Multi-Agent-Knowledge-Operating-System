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

## Stage 3: load into PostgreSQL

Needs Docker Desktop (or any PostgreSQL 16 with pgvector).

```bash
docker compose up -d                 # Postgres + pgvector and Redis
python -m pip install -r requirements.txt
alembic upgrade head                 # creates the 11 tables
python -m makos.data.load_bpi        # on Windows, first run:  set PYTHONPATH=backend
```

The loader bulk-loads with COPY (a few minutes for 1.6M events) and checks the
database counts against `data/profile/bpi2019_profile.json`. Use `--truncate`
to reload. Events dated outside 2017-01-01 to 2019-12-31 are kept and flagged
`ts_outlier`.

## Stage 4: baseline audit and splits

```bash
python -m makos.audit.baseline         # on Windows, first run:  set PYTHONPATH=backend
```

Applies the BPI matching rules (R1 value mismatch, R2 over PO value, R3 invoice
before goods receipt, R4 paid without goods receipt, R6 duplicate invoice) to
every PO line item. Writes candidate labels to `data/labels/` (not in git),
the fixed 60/20/20 split by purchase document to `data/splits/`, and a summary
to `data/profile/baseline_audit.md`. These are **candidate** labels until the
two-reviewer check.

## Stage 5: policy manuals

```bash
python data/scripts/download_policies.py   # saves PDFs to data/raw/policy/ and checks SHA-256
python -m makos.policy.ingest              # on Windows, first run:  set PYTHONPATH=backend
```

If a government site blocks the script, open the printed URL in a browser and
save the PDF into `data/raw/policy/` under the file name shown. For the 2024
edition use the official list at https://doe.gov.in/manuals ("Manual for
Procurement of Goods - Second Edition, 2024") and save it as
`Manual_for_Procurement_of_Goods_2024.pdf`.

The parser splits each manual into numbered clauses with edition, effective
date, page and parent heading, writes `data/interim/policy_clauses.parquet`,
and checks that every clause cited in `data/policy/policy_map.yaml` exists.
`policy_map.yaml` is a **draft** until two reviewers sign it off.

| Folder | Contents | In git? |
| --- | --- | --- |
| `raw/` | Downloaded source files | Only `CHECKSUMS.txt` |
| `interim/` | Parquet tables built from raw files | No |
| `profile/` | Profiling and baseline-audit reports | Yes |
| `labels/` | Candidate labels (parquet) | No |
| `splits/` | Train/val/test split by purchase document | Yes |
| `scripts/` | Download and processing code | Yes |

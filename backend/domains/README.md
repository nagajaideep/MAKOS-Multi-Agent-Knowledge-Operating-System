# Domain packs

MAKOS is a general framework. Everything that is specific to one use case
lives in a **domain pack**; the core never imports a pack by name.

```
backend/
  makos/core/        framework: database base + shared tables, document ingestion,
                     pack loader (later: orchestrator, CCL, agents, rules, approvals)
  domains/<pack>/    one folder per use case
    pack.yaml        the contract (below)
    models.py        the pack's business tables
    loader.py        loads the pack's real data into those tables
    policy_map.yaml  which document clause grounds each rule, per edition
    audit.py / rules (rules move to YAML for the KRN engine in stage 7)
```

| Pack | Status | Records | Documents |
| --- | --- | --- | --- |
| `bpi_p2p` | built (stages 1-5) | BPI Challenge 2019 purchase-to-pay log | Indian Manual for Procurement of Goods 2017/2022/2024, GFR 2017 |
| `federal_contracts` | next | USAspending awards, SAM.gov exclusions | FAR (eCFR point-in-time) |
| `airline_refunds` | planned | BTS on-time performance | DOT refund rule, airline customer-service plans |
| `finance` | stretch | SEC XBRL company facts | 10-K filings (FinanceBench) |

## pack.yaml contract

| Key | Required | Meaning |
| --- | --- | --- |
| `name` | yes | Must equal the folder name |
| `title`, `description` | yes | Shown in the UI |
| `entities` | yes | Business entities: `name`, `table`, `key` (the join key, e.g. supplier UEI) |
| `documents` | yes | `raw_dir` and `sources`, each with versioned `editions` (`effective_from`, `filename`, `url`, `sha256`) |
| `actions` | yes | What agents may propose: `requires_approval`, `allowed_roles` |
| `policy_map` | no | File mapping each rule to clauses per edition |
| `models_module` | no | Python module defining the pack's tables |
| `eval_sets` | no | Paths to labels and fixed splits |

Generic commands take the pack name:

```bash
python data/scripts/download_policies.py <pack>
python -m makos.core.documents.ingest --pack <pack>
```

Research question RQ5 measures how much configuration a new pack needs and
whether MAKOS's gains hold across packs, so keep packs free of core changes.

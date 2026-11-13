# Dataset register

Every dataset MAKOS uses, where it came from, its licence and what we may do
with it. Licences were checked at the source on 2026-11-13. MAKOS is an
academic, non-commercial project; two datasets below require that.

## Track A: the MAKOS workflow

| Dataset | Source | Version / date | Licence | Redistribute in repo? | Attribution |
| --- | --- | --- | --- | --- | --- |
| BPI Challenge 2019 | 4TU.ResearchData via figshare article 12715853, DOI 10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1 | `BPI_Challenge_2019.xes`, 728.6 MB, downloaded 2026-11-13 | CC BY 4.0 | Allowed; we use a download script because of size | van Dongen, B.F. (2019). BPI Challenge 2019. 4TU.ResearchData. |
| Manual for Procurement of Goods, 2017 | Dept. of Expenditure, Ministry of Finance, Govt. of India | Foreword dated 05.04.2017 | Govt. of India publication | Link + download script only | Cite the Ministry of Finance as source; quote accurately |
| Manual for Procurement of Goods, 2022 update | Same | Released 01.07.2022 | Govt. of India publication | Link + download script only | Same |
| Manual for Procurement of Goods, 2nd ed. 2024 | Same | OM dated 16.08.2024 | Govt. of India publication | Link + download script only | Same |
| General Financial Rules 2017 (amended to 31.07.2024) | Same | Amended to 31.07.2024 | Govt. of India publication | Link + download script only | Same |

## Track B: component benchmarks

| Dataset | Source | Licence | Redistribute in repo? | Notes |
| --- | --- | --- | --- | --- |
| INV-CDIP | github.com/salesforce/inv-cdip | CC BY-NC 4.0 (non-commercial) | No | Only the 350 labelled invoices have field labels |
| CUAD v1 | The Atticus Project (Hugging Face: theatticusproject/cuad-qa) | CC BY 4.0 | Yes, with attribution | 510 contracts, 13,000+ expert labels |
| BIRD Mini-Dev | github.com/bird-bench/mini_dev | CC BY-SA 4.0 | Yes, share-alike | 500 question-SQL pairs |
| BIPIA | github.com/microsoft/BIPIA | Code MIT; data subsets have their own licences | No | Web QA and Summarization may not be redistributed; we use Email, Table and Code QA |
| World Bank debarred firms | worldbank.org/debarr via OpenSanctions | CC BY-NC 4.0 (non-commercial) | No | 4,316 entities, last changed 2026-11-06 |

## Checksums

SHA-256 of downloaded files, so every teammate can confirm identical data.

| File | SHA-256 |
| --- | --- |
| BPI_Challenge_2019.xes | `af63bc687fc4152f2123b05c3af7772b37ef3fce2d3f67f812666c9e356baae7` |
| Manual_for_Procurement_of_Goods_2017.pdf (266 pages) | `9d4d7179170aea9effcec3d134e98c53785db548cd1b8b18b5e7ce6836621f9f` |
| Manual_for_Procurement_of_Goods_2022.pdf (289 pages) | `ac9e31c465496bccfd2aa221773645bf1edaa0786b1911ddd136bffa09d79b2b` |
| Manual_for_Procurement_of_Goods_2024.pdf (392 pages) | `351b1f6f4cde096e5be83a9e331ca0fa25c0ceda91596c2b4db6a028aaef3b4c` |
| GFR_2017_Amended_upto_31-07-2024.pdf (19 pages, ch. 6) | `be7bad84362c4ddb305f5cb8c800bd112bec613f4320097f69ec49ed85f0c87b` |

The same values are written to `data/raw/CHECKSUMS.txt` by the download scripts.

## Data quality notes (from `data/profile/bpi2019_profile.md`)

- All published counts reproduced: 251,734 cases, 76,349 purchase documents, 1,595,923 events, 42 activities.
- 97.15% of events fall in 2018, 2.83% in 2019 and 223 events in 2017. 97 events carry implausible years (1948, 1993, 2001, 2008, 2015, 2016, 2020). The loader keeps them and flags them as `ts_outlier` (outside 2017-01-01 to 2019-12-31).
- Item categories: 3-way invoice before GR 221,010; 3-way invoice after GR 15,182; consignment 14,498; 2-way 1,044.

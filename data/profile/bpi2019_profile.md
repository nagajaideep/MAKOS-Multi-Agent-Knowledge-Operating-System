# BPI Challenge 2019: data profile

## Checks against published figures

| Measure | Expected | Found | OK |
| --- | --- | --- | --- |
| cases | 251,734 | 251,734 | yes |
| purchase_documents | 76,349 | 76,349 | yes |
| events | 1,595,923 | 1,595,923 | yes |
| activities | 42 | 42 | yes |

## Overview

- Cases (PO line items): 251,734
- Events: 1,595,923
- Distinct activities: 42
- Purchase documents: 76,349
- Vendors: 1975
- Event time range: 1948-01-26T22:59:00+00:00 to 2020-04-09T21:59:00+00:00

## Item categories

| Category | Cases |
| --- | --- |
| 3-way match, invoice before GR | 221,010 |
| 3-way match, invoice after GR | 15,182 |
| Consignment | 14,498 |
| 2-way match | 1,044 |

## Events per year

| Year | Events |
| --- | --- |
| 1948 | 10 |
| 1993 | 9 |
| 2001 | 22 |
| 2008 | 45 |
| 2015 | 3 |
| 2016 | 6 |
| 2017 | 223 |
| 2018 | 1,550,468 |
| 2019 | 45,135 |
| 2020 | 2 |

## Activities

| Activity | Events |
| --- | --- |
| Record Goods Receipt | 314,097 |
| Create Purchase Order Item | 251,734 |
| Record Invoice Receipt | 228,760 |
| Vendor creates invoice | 219,919 |
| Clear Invoice | 194,393 |
| Record Service Entry Sheet | 164,975 |
| Remove Payment Block | 57,136 |
| Create Purchase Requisition Item | 46,592 |
| Receive Order Confirmation | 32,065 |
| Change Quantity | 21,449 |
| Change Price | 12,423 |
| Delete Purchase Order Item | 8,875 |
| Change Approval for Purchase Order | 7,541 |
| Cancel Invoice Receipt | 7,096 |
| Vendor creates debit memo | 6,255 |
| Change Delivery Indicator | 3,289 |
| Cancel Goods Receipt | 3,096 |
| SRM: In Transfer to Execution Syst. | 1,765 |
| SRM: Created | 1,628 |
| SRM: Complete | 1,628 |
| SRM: Awaiting Approval | 1,628 |
| SRM: Document Completed | 1,628 |
| SRM: Ordered | 1,628 |
| Release Purchase Order | 1,610 |
| SRM: Change was Transmitted | 1,440 |
| Reactivate Purchase Order Item | 543 |
| Block Purchase Order Item | 514 |
| Cancel Subsequent Invoice | 491 |
| Release Purchase Requisition | 467 |
| Change Storage Location | 415 |
| Update Order Confirmation | 244 |
| SRM: Deleted | 188 |
| Record Subsequent Invoice | 167 |
| Set Payment Block | 124 |
| SRM: Transfer Failed (E.Sys.) | 45 |
| Change Currency | 35 |
| Change Final Invoice Indicator | 11 |
| SRM: Transaction Completed | 8 |
| Change payment term | 7 |
| SRM: Incomplete | 6 |
| SRM: Held | 6 |
| Change Rejection Indicator | 2 |

## Events per case

- count: 251,734.0
- mean: 6.3
- std: 13.1
- min: 1.0
- 25%: 5.0
- 50%: 5.0
- 75%: 6.0
- max: 990.0

## Attributes found

Case: Company, Document Type, GR-Based Inv. Verif., Goods Receipt, Item, Item Category, Item Type, Name, Purch. Doc. Category name, Purchasing Document, Source, Spend area text, Spend classification text, Sub spend area text, Vendor, case_id

Event: Cumulative net worth (EUR), User, activity, case_id, org:resource, seq, time:timestamp

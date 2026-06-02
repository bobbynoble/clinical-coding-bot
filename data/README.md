# Reference Data

Drop your coding reference CSVs here before running `python -m app.indexer`.

## Required filenames and formats

### icd10.csv (ICD-10-CM)
Free download from CMS:
https://www.cms.gov/medicare/coding-billing/icd-10-codes

Use the "Order" file. Expected columns (case-insensitive):
- `code`
- `long description` (becomes `description`)
- `short description` (becomes `notes`)

### opcs4.csv (OPCS-4)
Requires NHS TRUD registration (free for NHS staff):
https://isd.digital.nhs.uk/trud/users/guest/filters/0/categories/26

Expected columns:
- `code`
- `description`

### hcc.csv (CMS HCC)
Free from CMS Risk Adjustment page:
https://www.cms.gov/medicare/health-plans/medicareadvtgspecratestats/risk-adjustors

Expected columns:
- `icd_10_cm_code`
- `icd_10_cm_code_description`
- `hcc_description`

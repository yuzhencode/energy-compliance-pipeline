# energy-compliance-pipeline

Automated regulatory reporting pipeline for Ofgem compliance data.

Built with Python, PostgreSQL, dbt, and AWS — inspired by real-world debt management
reporting workflows in the UK energy sector. All data is synthetic, generated with [Faker](https://faker.readthedocs.io/).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  PostgreSQL                                                  │
│  ┌──────────────┐  ┌──────────────────────────────────────┐ │
│  │  Raw layer   │  │  dbt layer                           │ │
│  │  accounts    │→ │  staging/stg_accounts                │ │
│  │  arrangements│  │  staging/stg_debt_arrangements       │ │
│  │  switches    │  │  marts/ofgem_summary                 │ │
│  │  report_runs │  │  marts/account_detail                │ │
│  └──────────────┘  └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
  Extractor (SQL → DataFrame)
         │
         ▼
  Transformer (DataFrame → Pydantic models)
         │
         ▼
  Validator (cross-row business rules)
         │
         ▼
  Reporter (styled Excel → S3)
```

### Data layers

| Layer | Location | Purpose |
|-------|----------|---------|
| **Raw** | `sql/schema.sql` | Source-faithful tables, no business logic |
| **Staging** | `energy_compliance/models/staging/` | Normalise, cast types, derive flags |
| **Mart** | `energy_compliance/models/marts/` | Aggregated, report-ready output |

---

## Regulatory Context

This pipeline models the data workflows required for Ofgem's
**Social Obligations Reporting** — a mandatory quarterly submission
for all licensed UK energy suppliers.

Report fields map directly to published Ofgem indicators:

| Field | Ofgem Indicator |
|-------|----------------|
| `avg_debt_no_arrangement_gbp` | Average debt level — no arrangement (arrears) |
| `avg_debt_with_arrangement_gbp` | Average debt level — with arrangement |
| `pct_repaying_via_ppm` | Proportion repaying via PPM (%) |
| `accounts_with_debt` | Number of accounts with energy debt |
| `accounts_no_arrangement` | Accounts in arrears, no repayment plan |
| `total_debt_over_91_days_gbp` | Total financial value of debt >91 days |

**Sources**
- [Ofgem Indicators Timetable Jan–Mar 2026](https://www.ofgem.gov.uk/sites/default/files/2026-01/Ofgem%20indicators%20publication%20timetable%20January%20to%20March%202026.pdf)
- [Ofgem Debt & Arrears Indicators](https://www.ofgem.gov.uk/data/debt-and-arrears-indicators)
- [Ofgem Debt Strategy Update, Nov 2025](https://www.ofgem.gov.uk/policy/debt-strategy-update-supporting-reduction-energy-debt)

---

## Phases

| Phase | Status | Description |
|-------|--------|-------------|
| **1 — ETL pipeline** | ✅ Complete | Python + SQL, Pydantic models, Excel output, S3, CI/CD |
| **2 — dbt quality layer** | ✅ Complete | dbt models, 17 data quality tests, staging + mart layers |
| **3 — RAG compliance assistant** | 🔜 Planned | LangChain + Ofgem docs Q&A |

---

## Quickstart

### Prerequisites
- Python 3.12+
- PostgreSQL 15+
- dbt-core 1.8+ (`pip install dbt-postgres==1.8.2`)
- AWS CLI configured (`aws configure`) — optional, for S3 upload

### 1. Clone & install

```bash
git clone https://github.com/yuzhencode/energy-compliance-pipeline.git
cd energy-compliance-pipeline
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

### 3. Set up database

```bash
createdb energy_compliance
psql energy_compliance -f sql/schema.sql
python seeds/generate_seeds.py
```

### 4. Run dbt models and tests

```bash
cd energy_compliance
dbt run      # builds staging views + mart tables
dbt test     # runs 17 data quality tests
cd ..
```

### 5. Run the pipeline

```bash
python run_pipeline.py --no-upload
# Output: outputs/ofgem_report_YYYY-MM-DD.xlsx
```

### 6. Run Python tests

```bash
pytest tests/ -v
```

---

## dbt Data Quality Tests

17 tests covering Ofgem reporting requirements:

| Test | Model | Ofgem Relevance |
|------|-------|----------------|
| `unique` + `not_null` | `stg_accounts.account_id` | Account identifiability |
| `accepted_values` | `stg_accounts.fuel_type` | Data standardisation |
| `accepted_values` | `stg_accounts.payment_method` | Data standardisation |
| `accepted_values` | `stg_accounts.account_status` | Valid status values |
| `not_null` | `stg_accounts.debt_amount_gbp` | Debt amount completeness |
| `unique` + `not_null` | `stg_debt_arrangements.arrangement_id` | Arrangement integrity |
| `unique` + `not_null` | `account_detail.account_id` | No duplicate submissions |
| `not_null` | `account_detail.debt_amount_gbp` | Debt completeness |
| `accepted_values` | `account_detail.fuel_type` | Data standardisation |
| `not_null` | `ofgem_summary.accounts_with_debt` | Core indicator completeness |
| `not_null` | `ofgem_summary.pct_repaying_via_ppm` | PPM indicator completeness |
| `not_null` | `ofgem_summary.report_date` | Submission date required |

---

## CI/CD

GitHub Actions runs on every push to `main` or `develop`:

1. Spins up PostgreSQL service container
2. Installs dependencies
3. Runs schema migration + seed (200 rows)
4. Runs `pytest`
5. Runs full pipeline smoke test (`--no-upload`)

On merge to `main`, a second deploy job runs the pipeline and uploads the report to S3.

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key |
| `AWS_S3_BUCKET` | Target S3 bucket name |

---

## Project structure

```
energy-compliance-pipeline/
├── .github/workflows/ci.yml
├── energy_compliance/              # dbt project (Phase 2)
│   ├── models/
│   │   ├── staging/
│   │   │   ├── sources.yml
│   │   │   ├── schema.yml
│   │   │   ├── stg_accounts.sql
│   │   │   └── stg_debt_arrangements.sql
│   │   └── marts/
│   │       ├── schema.yml
│   │       ├── ofgem_summary.sql   # 6 Ofgem quarterly indicators
│   │       └── account_detail.sql
│   └── dbt_project.yml
├── pipeline/
│   ├── models.py       # Pydantic schema models (OOP data layer)
│   ├── extractor.py    # SQL → DataFrame
│   ├── transformer.py  # DataFrame → validated Pydantic models
│   ├── validator.py    # Cross-row business rules
│   └── reporter.py     # Excel generation + S3 upload
├── sql/
│   ├── schema.sql              # Raw layer table definitions
│   ├── staging/                # Pre-dbt SQL (reference only)
│   └── marts/                  # Pre-dbt SQL (reference only)
├── seeds/
│   └── generate_seeds.py
├── tests/
│   ├── conftest.py
│   ├── test_models.py
│   └── test_validator.py
├── config.py
├── logger.py
├── run_pipeline.py
├── requirements.txt
└── .env.example
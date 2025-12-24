# Conto Test App

A sandbox FastAPI application designed for testing [Conto](https://github.com/conto-ai/conto) PR review signals.

## Overview

This repository is intentionally structured to trigger Conto's two MVP signals:

1. **Hotspot Risk**: Historical churn detection on frequently modified files
2. **Coverage Attention Gap**: Detection of modified lines lacking test coverage

The app also demonstrates Conto's "quiet presence" feature: a non-blocking GitHub Check Run appears on every PR, even when no comment is posted.

## Repository Structure

```
conto-test-app/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API endpoints (/quote, /charge)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── pricing.py       # HOTSPOT CANDIDATE - touch frequently
│   │   ├── policy.py        # UNDER-TESTED - has uncovered branches
│   │   └── utils.py         # Well-tested utilities
│   └── services/
│       ├── __init__.py
│       ├── billing.py       # Orchestrates pricing/policy
│       └── fraud.py         # Has uncovered branches
├── tests/
│   ├── test_routes.py
│   ├── test_utils.py
│   └── test_billing.py
├── .github/
│   └── workflows/
│       └── ci.yml           # Runs pytest + uploads coverage.xml
├── pyproject.toml
├── README.md
└── .gitignore
```

## Setup

### Prerequisites

- Python 3.11+

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_ORG/conto-test-app.git
cd conto-test-app

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Running the App

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### Running Tests

```bash
# Run tests
pytest

# Run tests with coverage
coverage run -m pytest
coverage report
coverage xml  # Generates coverage.xml for Conto
```

## API Endpoints

### POST /quote

Generate a price quote for an order.

**Request:**
```json
{
  "user_id": "user-123",
  "tier": "free",
  "region": "EU",
  "items": [
    {"sku": "ITEM-1", "qty": 2, "unit_price": 50.0}
  ],
  "coupon": "SAVE10"
}
```

**Response:**
```json
{
  "subtotal": 100.0,
  "discount": 10.0,
  "tax": 18.0,
  "total": 108.0,
  "currency": "USD"
}
```

### POST /charge

Process a payment charge with fraud risk assessment.

**Request:**
```json
{
  "user_id": "user-123",
  "amount": 100.0,
  "currency": "USD",
  "payment_method": "card",
  "region": "EU"
}
```

**Response:**
```json
{
  "approved": true,
  "reason": "Transaction approved",
  "risk_score": 0.15
}
```

---

## Conto Test Scenarios

After installing Conto on this repository, use these scenarios to trigger different signals.

### Scenario A: No Unusual Risk (Check Run Only)

**Purpose:** Verify Conto's quiet presence - a Check Run appears without posting a PR comment.

**Steps:**
1. Create a new branch:
   ```bash
   git checkout -b docs/update-readme
   ```

2. Make a trivial change (update this README or a docstring):
   ```bash
   echo "\n<!-- Updated: $(date) -->" >> README.md
   ```

3. Commit and push:
   ```bash
   git add README.md
   git commit -m "docs: update README"
   git push -u origin docs/update-readme
   ```

4. Open a Pull Request to `main`.

**Expected Result:**
- Conto Check Run appears with status "No unusual risk detected"
- No PR comment is posted
- On your first PR, you may see a Conto onboarding comment

---

### Scenario B: Hotspot Risk

**Purpose:** Trigger the Hotspot Risk signal by modifying a frequently-changed file.

#### Step 1: Build Churn History

Create and merge 6-10 small PRs that touch `app/core/pricing.py`:

```bash
# PR 1: Add a comment
git checkout main && git pull
git checkout -b churn/pricing-1
echo "# Pricing update 1" >> app/core/pricing.py
git add . && git commit -m "churn: pricing update 1"
git push -u origin churn/pricing-1
# Open PR and merge

# PR 2: Another small change
git checkout main && git pull
git checkout -b churn/pricing-2
sed -i '' 's/# Pricing update 1/# Pricing update 2/' app/core/pricing.py
git add . && git commit -m "churn: pricing update 2"
git push -u origin churn/pricing-2
# Open PR and merge

# Repeat 4-8 more times with variations:
# - Adjust TAX_RATES values slightly
# - Modify MIN_ORDER_AMOUNTS
# - Add/remove comments
# - Rename a variable and rename it back
```

**Quick churn script (run multiple times):**
```bash
N=$(($(date +%s) % 100))
git checkout main && git pull
git checkout -b "churn/pricing-$N"
echo "# Churn marker $N" >> app/core/pricing.py
git add . && git commit -m "churn: pricing update $N"
git push -u origin "churn/pricing-$N"
```

#### Step 2: Trigger Hotspot Detection

After merging 6-10 churn PRs:

```bash
git checkout main && git pull
git checkout -b feature/pricing-change
```

Make a meaningful change to `app/core/pricing.py`:
```python
# In calculate_tax(), change the default rate:
rate = TAX_RATES.get(region, 0.10)  # Changed from 0.08
```

```bash
git add . && git commit -m "feat: adjust default tax rate"
git push -u origin feature/pricing-change
```

Open a PR.

**Expected Result:**
- Conto PR comment highlighting `app/core/pricing.py` as a hotspot
- Comment includes churn history context

---

### Scenario C: Coverage Attention Gap

**Purpose:** Trigger the Coverage Attention Gap signal by modifying untested code.

**Background:** The following branches are intentionally NOT covered by tests:
- `app/core/policy.py`: APAC region, weekend logic (weekday >= 5), invalid coupon
- `app/services/fraud.py`: APAC + invoice combination

**Steps:**

1. Create a feature branch:
   ```bash
   git checkout main && git pull
   git checkout -b feature/apac-discount
   ```

2. Modify an uncovered branch in `app/core/policy.py`. For example, change the APAC multiplier:
   ```python
   # Around line 62, change:
   if region == "APAC":
       # APAC customers get boosted discounts
       multiplier = REGION_MULTIPLIERS["APAC"]
       discount = round_money(discount * multiplier)
   ```

   To:
   ```python
   if region == "APAC":
       # APAC customers get boosted discounts (increased)
       multiplier = REGION_MULTIPLIERS["APAC"] * 1.1
       discount = round_money(discount * multiplier)
   ```

3. **Do NOT add tests** for this change.

4. Commit and push:
   ```bash
   git add . && git commit -m "feat: increase APAC discount multiplier"
   git push -u origin feature/apac-discount
   ```

5. Open a Pull Request.

**Expected Result:**
- Conto PR comment highlighting uncovered modified lines
- The comment shows which lines in the diff lack test coverage

**Alternative targets for Scenario C:**
- Modify the weekend bonus logic (lines with `if weekday >= 5`)
- Modify the invalid coupon branch (`else` after coupon validation)
- Modify `fraud.py` APAC + invoice handling

---

## Notes

### Intentional Coverage Gaps

This repository intentionally contains under-tested branches to enable testing Conto's Coverage Attention Gap signal:

| File | Uncovered Branch | How to Trigger |
|------|------------------|----------------|
| `policy.py` | APAC region logic | Modify lines 60-65 |
| `policy.py` | Weekend bonus | Modify lines 54-57 |
| `policy.py` | Invalid coupon | Modify lines 48-50 |
| `policy.py` | Enterprise tier | Modify `is_eligible_for_promotion` |
| `fraud.py` | APAC + invoice | Modify lines 55-58 |
| `fraud.py` | Medium risk + high amount | Modify `should_require_verification` |

### CI Configuration

The GitHub Actions workflow (`.github/workflows/ci.yml`):
- Runs on `pull_request` and `push` to `main`
- Uses Python 3.11
- Runs `coverage run -m pytest`
- Generates `coverage.xml`
- Uploads as artifact named `coverage-xml`

Conto reads this artifact to analyze coverage on modified lines.

### Local Coverage Report

To see current coverage locally:

```bash
coverage run -m pytest
coverage report --show-missing
```

This shows which lines are not covered by tests.

## License

MIT

#!/usr/bin/env bash
#
# Scenario B - Step 2: Trigger Hotspot Detection
#
# Purpose: After building churn history, make a meaningful change to trigger hotspot
# Prerequisites: Run scenario_b_prime.sh 6-10 times first
#
set -e

BRANCH_NAME="smoke/scenario-b-hotspot-$(date +%s)"

echo "=== Scenario B: Trigger Hotspot Detection ==="
echo ""
echo "This script makes a meaningful change to pricing.py after churn priming."
echo "Prerequisites: You should have merged 6-10 churn PRs first."
echo ""

# Check churn history
echo "Checking churn history for pricing.py..."
CHURN_COUNT=$(git log --oneline --all -- app/core/pricing.py | wc -l | tr -d ' ')
echo "Found $CHURN_COUNT commits touching pricing.py"

if [ "$CHURN_COUNT" -lt 6 ]; then
  echo ""
  echo "WARNING: Only $CHURN_COUNT commits found. Recommended: 6+ commits."
  echo "Run scenario_b_prime.sh more times to build churn history."
  read -p "Continue anyway? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# Ensure we're on main and up to date
git checkout main
git pull origin main

# Create feature branch
echo ""
echo "Creating branch: $BRANCH_NAME"
git checkout -b "$BRANCH_NAME"

# Make a meaningful change to pricing.py
cat > /tmp/pricing_patch.py << 'PATCH'
# Apply a meaningful change: adjust default tax rate and add new function
PATCH

# Change the default tax rate
sed -i '' 's/rate = TAX_RATES.get(region, 0.08)/rate = TAX_RATES.get(region, 0.10)  # Increased default rate/' app/core/pricing.py

# Add a new helper function before the last function
sed -i '' '/^def apply_bulk_discount/i\
\
def estimate_shipping(region: str, item_count: int) -> float:\
    """Estimate shipping cost based on region and item count."""\
    base_rates = {"EU": 5.0, "US": 4.0, "APAC": 8.0}\
    base = base_rates.get(region, 5.0)\
    return round_money(base + (item_count * 0.5))\
\
' app/core/pricing.py

# Commit and push
git add app/core/pricing.py
git commit -m "feat: adjust default tax rate and add shipping estimation"
git push -u origin "$BRANCH_NAME"

# Create PR
echo ""
echo "Creating Pull Request..."
PR_URL=$(gh pr create \
  --title "Smoke Test B: Hotspot Risk - Pricing Changes" \
  --body "$(cat <<'EOF'
## Smoke Test: Scenario B - Hotspot Risk

**Purpose:** Trigger Conto's Hotspot Risk signal

**Changes to `app/core/pricing.py`:**
- Increased default tax rate from 8% to 10%
- Added new `estimate_shipping()` function

**Expected Conto Behavior:**
- [ ] PR comment highlighting `pricing.py` as a churn hotspot
- [ ] Comment includes historical context about frequent changes

**Churn History:**
This file has been modified in multiple recent PRs to build churn history.

---
*Automated smoke test - review Conto's response before closing*
EOF
)" \
  --head "$BRANCH_NAME" \
  --base main)

echo ""
echo "=== PR Created ==="
echo "$PR_URL"
echo ""
echo "Next steps:"
echo "1. Wait for CI to complete"
echo "2. Verify Conto PR comment about hotspot risk"
echo "3. Review the hotspot context in the comment"
echo "4. Close the PR (don't merge - reverts test changes)"

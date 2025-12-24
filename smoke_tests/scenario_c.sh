#!/usr/bin/env bash
#
# Scenario C: Coverage Attention Gap
#
# Purpose: Modify uncovered code to trigger coverage gap detection
# Expected: Conto PR comment highlighting uncovered modified lines
#
set -e

BRANCH_NAME="smoke/scenario-c-coverage-$(date +%s)"
TARGET=${1:-policy}  # 'policy' or 'fraud'

echo "=== Scenario C: Coverage Attention Gap ==="
echo ""
echo "This script modifies uncovered branches to trigger Conto's coverage signal."
echo "Target module: $TARGET"
echo ""

# Ensure we're on main and up to date
git checkout main
git pull origin main

# Create feature branch
echo "Creating branch: $BRANCH_NAME"
git checkout -b "$BRANCH_NAME"

if [ "$TARGET" = "fraud" ]; then
  # Modify uncovered APAC + invoice branch in fraud.py
  echo "Modifying uncovered APAC+invoice branch in fraud.py..."

  sed -i '' 's/base_risk += 0.25/base_risk += 0.30  # Increased APAC invoice scrutiny/' app/services/fraud.py
  sed -i '' 's/flags.append("apac_invoice_review")/flags.append("apac_invoice_high_scrutiny")/' app/services/fraud.py

  CHANGED_FILE="app/services/fraud.py"
  CHANGE_DESC="Increased APAC invoice risk assessment from 0.25 to 0.30"
else
  # Modify uncovered APAC branch in policy.py (default)
  echo "Modifying uncovered APAC discount branch in policy.py..."

  sed -i '' 's/multiplier = REGION_MULTIPLIERS\["APAC"\]/multiplier = REGION_MULTIPLIERS["APAC"] * 1.15  # Boosted APAC discount/' app/core/policy.py

  CHANGED_FILE="app/core/policy.py"
  CHANGE_DESC="Increased APAC discount multiplier by 15%"
fi

# Commit and push (intentionally NOT adding tests)
git add "$CHANGED_FILE"
git commit -m "feat: enhance $TARGET logic for APAC region

Note: No tests added - this change modifies an uncovered branch."
git push -u origin "$BRANCH_NAME"

# Create PR
echo ""
echo "Creating Pull Request..."
PR_URL=$(gh pr create \
  --title "Smoke Test C: Coverage Gap - $TARGET changes" \
  --body "$(cat <<EOF
## Smoke Test: Scenario C - Coverage Attention Gap

**Purpose:** Trigger Conto's Coverage Attention Gap signal

**Changed File:** \`$CHANGED_FILE\`

**Change:** $CHANGE_DESC

**Important:** No tests were added for this change. The modified lines are in
a branch that is intentionally not covered by existing tests.

**Expected Conto Behavior:**
- [ ] PR comment highlighting uncovered modified lines
- [ ] Comment shows which specific lines lack test coverage
- [ ] Coverage percentage for changed lines shown

**Uncovered branches in this file:**
- APAC region handling
- Weekend discount logic
- Invalid coupon handling

---
*Automated smoke test - review Conto's coverage analysis before closing*
EOF
)" \
  --head "$BRANCH_NAME" \
  --base main)

echo ""
echo "=== PR Created ==="
echo "$PR_URL"
echo ""
echo "Next steps:"
echo "1. Wait for CI to complete (coverage.xml must be generated)"
echo "2. Verify Conto PR comment about coverage gap"
echo "3. Check that modified lines are flagged as uncovered"
echo "4. Close the PR (don't merge - keeps intentional coverage gaps)"

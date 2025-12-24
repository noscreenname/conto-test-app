#!/usr/bin/env bash
#
# Scenario B - Step 1: Build Churn History
#
# Purpose: Create multiple small PRs touching pricing.py to build churn history
# Run this script 6-10 times, merging each PR before running the next
#
set -e

ITERATION=${1:-$(date +%s)}
BRANCH_NAME="churn/pricing-$ITERATION"

echo "=== Scenario B: Building Churn History (Iteration: $ITERATION) ==="
echo ""
echo "This script creates a small change to pricing.py to build churn history."
echo "Run this 6-10 times (merging each PR) before running scenario_b_trigger.sh"
echo ""

# Ensure we're on main and up to date
git checkout main
git pull origin main

# Create feature branch
echo "Creating branch: $BRANCH_NAME"
git checkout -b "$BRANCH_NAME"

# Make a small change to pricing.py
# Rotate through different minor changes
CHANGE_TYPE=$((ITERATION % 5))

case $CHANGE_TYPE in
  0)
    # Add a comment
    sed -i '' "s/# Tax rates by region/# Tax rates by region (updated $ITERATION)/" app/core/pricing.py
    ;;
  1)
    # Modify a docstring slightly
    sed -i '' "s/Calculate the subtotal/Calculate the order subtotal/" app/core/pricing.py
    ;;
  2)
    # Revert docstring
    sed -i '' "s/Calculate the order subtotal/Calculate the subtotal/" app/core/pricing.py
    ;;
  3)
    # Update comment
    sed -i '' "s/# Tax rates by region (updated [0-9]*)/# Tax rates by region/" app/core/pricing.py
    ;;
  4)
    # Add trailing comment
    echo "# Churn marker: $ITERATION" >> app/core/pricing.py
    ;;
esac

# Commit and push
git add app/core/pricing.py
git commit -m "churn: pricing update iteration $ITERATION"
git push -u origin "$BRANCH_NAME"

# Create PR
echo ""
echo "Creating Pull Request..."
PR_URL=$(gh pr create \
  --title "Churn: Pricing Update $ITERATION" \
  --body "$(cat <<'EOF'
## Churn Building PR

Part of Scenario B smoke test - building churn history for `pricing.py`.

**Auto-merge recommended** - this is a trivial change.

---
*Automated smoke test for Conto hotspot detection*
EOF
)" \
  --head "$BRANCH_NAME" \
  --base main)

echo ""
echo "=== PR Created ==="
echo "$PR_URL"
echo ""
echo "Next steps:"
echo "1. Merge this PR (use: gh pr merge --merge)"
echo "2. Run this script again with a new iteration number"
echo "3. After 6-10 iterations, run scenario_b_trigger.sh"
echo ""
echo "Quick merge command:"
echo "  gh pr merge --merge --delete-branch"

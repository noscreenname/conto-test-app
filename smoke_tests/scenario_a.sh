#!/usr/bin/env bash
#
# Scenario A: No Unusual Risk
#
# Purpose: Verify Conto's quiet presence - Check Run appears without PR comment
# Expected: Conto Check Run shows "No unusual risk detected", no PR comment
#
set -e

BRANCH_NAME="smoke/scenario-a-$(date +%s)"

echo "=== Scenario A: No Unusual Risk ==="
echo ""
echo "This script creates a trivial change (README update) that should NOT"
echo "trigger any Conto signals - only a Check Run with 'no unusual risk'."
echo ""

# Ensure we're on main and up to date
git checkout main
git pull origin main

# Create feature branch
echo "Creating branch: $BRANCH_NAME"
git checkout -b "$BRANCH_NAME"

# Make a trivial change to README
echo "" >> README.md
echo "<!-- Smoke test: $(date -u +%Y-%m-%dT%H:%M:%SZ) -->" >> README.md

# Commit and push
git add README.md
git commit -m "docs: smoke test scenario A - trivial README update"
git push -u origin "$BRANCH_NAME"

# Create PR
echo ""
echo "Creating Pull Request..."
PR_URL=$(gh pr create \
  --title "Smoke Test A: No Unusual Risk" \
  --body "$(cat <<'EOF'
## Smoke Test: Scenario A

**Purpose:** Verify Conto's quiet presence

**Change:** Trivial README comment update

**Expected Conto Behavior:**
- [ ] Check Run appears with status "No unusual risk detected"
- [ ] No PR comment is posted (unless this is the first PR - onboarding comment)

---
*Automated smoke test - safe to close/merge*
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
echo "2. Verify Conto Check Run shows 'no unusual risk'"
echo "3. Verify NO Conto PR comment (unless first PR)"
echo "4. Close or merge the PR"

# Smoke Tests for Conto

Automated scripts to test Conto's PR review signals.

## Prerequisites

- GitHub CLI (`gh`) installed and authenticated
- Repository cloned and set as origin
- Conto installed on the repository

## Scripts

### Scenario A: No Unusual Risk

Tests Conto's "quiet presence" - verifies that a trivial change only shows a Check Run.

```bash
./smoke_tests/scenario_a.sh
```

**Expected:** Check Run with "no unusual risk", no PR comment.

---

### Scenario B: Hotspot Risk

Tests Conto's churn hotspot detection. Requires two steps:

#### Step 1: Build Churn History

Run this 6-10 times, merging each PR:

```bash
./smoke_tests/scenario_b_prime.sh 1
# Merge PR, then:
./smoke_tests/scenario_b_prime.sh 2
# Merge PR, then:
./smoke_tests/scenario_b_prime.sh 3
# ... repeat until you have 6-10 merged PRs
```

Quick merge after each:
```bash
gh pr merge --merge --delete-branch
```

#### Step 2: Trigger Hotspot Detection

After building churn history:

```bash
./smoke_tests/scenario_b_trigger.sh
```

**Expected:** PR comment highlighting `pricing.py` as a hotspot.

---

### Scenario C: Coverage Attention Gap

Tests Conto's coverage gap detection on modified lines.

```bash
# Modify policy.py (default)
./smoke_tests/scenario_c.sh

# Or modify fraud.py
./smoke_tests/scenario_c.sh fraud
```

**Expected:** PR comment showing uncovered modified lines.

---

## Quick Full Test

```bash
# Scenario A
./smoke_tests/scenario_a.sh
# Check PR, then close it

# Scenario B (abbreviated - 3 churn PRs)
for i in 1 2 3; do
  ./smoke_tests/scenario_b_prime.sh $i
  gh pr merge --merge --delete-branch
  sleep 5
done
./smoke_tests/scenario_b_trigger.sh
# Check PR for hotspot signal, then close it

# Scenario C
./smoke_tests/scenario_c.sh
# Check PR for coverage gap signal, then close it
```

## Cleanup

Close all smoke test PRs:
```bash
gh pr list --state open --json number,title | \
  jq -r '.[] | select(.title | startswith("Smoke Test") or startswith("Churn:")) | .number' | \
  xargs -I {} gh pr close {}
```

Delete smoke test branches:
```bash
git branch -r | grep -E 'smoke/|churn/' | sed 's/origin\///' | xargs -I {} git push origin --delete {}
```

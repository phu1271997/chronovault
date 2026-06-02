# Deploying ChronoVault In GenLayer Studio

This guide assumes you are deploying from the files in `/Users/peter/AI/ChronoVault`.

## 1. Open Studio

Open:

https://studio.genlayer.com/run-debug

## 2. Reset The Studio Session

Before deploying anything:

1. Open Settings.
2. Click **Reset Storage**.
3. Confirm the reset.
4. Hard refresh the browser:
   - macOS: `Cmd+Shift+R`
   - Windows/Linux: `Ctrl+Shift+F5`

This avoids stale storage and old dependency state.

## 3. Deploy The Sanity Contract First

Deploy:

```text
contracts/storage_test.py
```

After deployment, click the transaction in the Studio sidebar.

Verify:

```text
Result: SUCCESS
```

Do not rely only on:

```text
Status: FINALIZED
```

A finalized transaction can still contain an execution error. Always inspect the transaction result.

Run:

```python
increment_and_store("studio sanity check")
```

Then run:

```python
get_state()
```

Expected result contains:

```json
{
  "counter": 1,
  "stored_text": "studio sanity check"
}
```

Only continue if this contract succeeds.

## 4. Deploy The Main Contract

Deploy:

```text
contracts/chronovault.py
```

Click the deployment transaction in the sidebar and verify:

```text
Result: SUCCESS
```

If you see `Result: ERROR`, inspect the traceback and compare it with the checklist below.

## 5. Minimal Happy-Path Walkthrough

Use placeholder addresses and URLs that are valid in your Studio environment.

### Record A Sanction

```python
record_sanction(
  "0xOFFENDER_ADDRESS",
  "Rug-pulled DAO treasury and ignored restitution requests",
  "https://example.com/original-sanction-report",
  4,
  1710000000
)
```

Expected:

```text
1
```

Then:

```python
check_address_status("0xOFFENDER_ADDRESS")
```

Expected:

```text
ACTIVE
```

### Try A Premature Petition

```python
petition_for_redemption(
  1,
  ["https://example.com/recent-good-post"],
  "https://etherscan.io/address/0xOFFENDER_ADDRESS",
  1710000100
)
```

Expected:

```text
Cooldown has not elapsed
```

### Simulate Cooldown Elapsed

The default cooldown is `15552000` seconds, or 180 days.

Call with a timestamp after:

```text
1725552000
```

Example:

```python
petition_for_redemption(
  1,
  [
    "https://example.com/restitution-receipts",
    "https://example.com/dao-contribution-history",
    "https://example.com/public-apology-and-followup"
  ],
  "https://etherscan.io/address/0xOFFENDER_ADDRESS",
  1742000000
)
```

Expected:

The result is a JSON petition record with one of:

```text
REDEEMED
CONDITIONAL_REDEMPTION
DENIED_WITH_PATH
DENIED
```

For strong sustained evidence, expect:

```text
REDEEMED
```

Click the transaction in the sidebar and verify:

```text
Result: SUCCESS
```

### Weak Petition

Record a second sanction, wait past cooldown by timestamp, then submit only a vague personal blog or inaccessible URL.

Expected:

```text
DENIED_WITH_PATH
```

or:

```text
DENIED
```

The AI reasoning should cite missing or weak evidence.

### Issuer Appeal

If the latest petition returned `REDEEMED` or `CONDITIONAL_REDEMPTION`, call:

```python
appeal_verdict(
  1,
  "Issuer believes the petition overstates restitution and ignores unresolved victims.",
  1742100000
)
```

Expected:

A JSON appeal result with a stricter re-evaluation verdict. Click the transaction and verify `Result: SUCCESS`.

## 6. Required Transaction Inspection

After every write call:

1. Click the transaction in the sidebar.
2. Verify `Result: SUCCESS`.
3. If `Result: ERROR`, read the traceback.

Common mappings:

| Symptom | Likely Cause |
| --- | --- |
| `Contract Queues not found` | Missing or wrong line 1 or line 2 header |
| `Contract IdlenessPhase not found` | Studio loaded old GenLayer version |
| `AttributeError: module 'genlayer' has no attribute 'Contract'` | Used `import genlayer` instead of `from genlayer import *` |
| `AssertionError: Is right the same storage type? TreeMap <- TreeMap` | Reassigned `TreeMap()` or `DynArray()` in `__init__` |
| Schema parser rejects contract | Public signature used unsupported type like `float`, `list`, `dict`, or custom class |
| Nondeterministic call crashes | `gl.nondet.*` was called outside `gl.vm.run_nondet_unsafe` |

## 7. Studio Rules Checklist

Every `.py` contract must satisfy:

```text
Line 1 exactly: # v0.2.16
Line 2 exactly: # { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
Only GenLayer import line: from genlayer import *
Main class named Contract
No TreeMap() or DynArray() assignment in __init__
No float public method signatures
Storage uses TreeMap/DynArray, not dict/list
Every gl.nondet.* call is inside gl.vm.run_nondet_unsafe
Time values are Unix seconds
Complex records are JSON strings
```

## 8. Manual Tests

After deployment, run the scenarios in:

```text
tests/manual_test_cases.md
```

The manual tests cover happy path, offender self-petition, third-party advocacy, weak evidence, conditional redemption, severe harm, and appeal.

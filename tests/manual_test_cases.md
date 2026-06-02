# ChronoVault Manual Test Cases

These tests are designed for GenLayer Studio. After every write call, click the transaction in the sidebar and verify `Result: SUCCESS`, not only `Status: FINALIZED`.

Use real public URLs when running the tests. The example URLs below are placeholders that describe the expected evidence category.

## Test 1: Happy Path, Genuine Change After Rug Pull

### Setup State

Issuer is the deployer. Offender address:

```text
0x1000000000000000000000000000000000000001
```

### Calls

```python
record_sanction(
  "0x1000000000000000000000000000000000000001",
  "Rug-pulled DAO treasury, then disappeared from community channels",
  "https://example.com/original-rug-pull-report",
  4,
  1710000000
)
```

Then petition after more than one year:

```python
petition_for_redemption(
  1,
  [
    "https://example.com/restitution-receipts-over-12-months",
    "https://example.com/public-apology-with-victim-responses",
    "https://example.com/dao-contributions-sustained-history"
  ],
  "https://etherscan.io/address/0x1000000000000000000000000000000000000001",
  1742000000
)
```

### Expected Verdict

```text
REDEEMED
```

### Why

The supporting evidence should show restitution, public accountability, and sustained positive contributions over a long period. The AI should reward patterns over isolated events and score recidivism risk low.

## Test 2: Edge Case, Offender Petitions For Themselves

### Setup State

Record a medium-severity sanction against:

```text
0x2000000000000000000000000000000000000002
```

### Calls

```python
record_sanction(
  "0x2000000000000000000000000000000000000002",
  "Repeated governance spam and abusive contributor behavior",
  "https://example.com/original-governance-incident",
  2,
  1710000000
)
```

From the offender's wallet, call:

```python
petition_for_redemption(
  2,
  [
    "https://example.com/offender-public-apology",
    "https://example.com/offender-constructive-governance-contributions"
  ],
  "https://etherscan.io/address/0x2000000000000000000000000000000000000002",
  1727000000
)
```

### Expected Verdict

```text
CONDITIONAL_REDEMPTION
```

or:

```text
REDEEMED
```

### Why

The contract does not require a third-party petitioner. The verdict depends only on evidence quality. For a medium-severity behavior issue with visible improvement, conditional or full redemption should be possible.

## Test 3: Edge Case, Third-Party Advocate Petitions

### Setup State

Record a sanction against:

```text
0x3000000000000000000000000000000000000003
```

### Calls

```python
record_sanction(
  "0x3000000000000000000000000000000000000003",
  "Contributor blacklisted after mishandling multisig communications",
  "https://example.com/original-multisig-communications-report",
  3,
  1710000000
)
```

From an advocate's wallet, call:

```python
petition_for_redemption(
  3,
  [
    "https://example.com/advocate-letter-with-specific-evidence",
    "https://example.com/offender-new-multisig-audit-trail",
    "https://example.com/community-feedback-thread"
  ],
  "https://etherscan.io/address/0x3000000000000000000000000000000000000003",
  1727000000
)
```

### Expected Verdict

```text
CONDITIONAL_REDEMPTION
```

### Why

Third-party advocacy is allowed. A reasonable result is conditional redemption when evidence is positive but the original issue involved trust and operational responsibility.

## Test 4: Sad Path, No Behavior Change

### Setup State

Record a sanction against:

```text
0x4000000000000000000000000000000000000004
```

### Calls

```python
record_sanction(
  "0x4000000000000000000000000000000000000004",
  "Phishing campaign targeting DAO members",
  "https://example.com/original-phishing-report",
  5,
  1710000000
)
```

After cooldown:

```python
petition_for_redemption(
  4,
  [
    "https://example.com/short-vague-redemption-statement"
  ],
  "https://etherscan.io/address/0x4000000000000000000000000000000000000004",
  1727000000
)
```

### Expected Verdict

```text
DENIED
```

### Why

There is no concrete behavior change, no restitution, and no evidence of reduced recidivism risk. Because the original sanction is severe, ambiguity should bias toward denial.

## Test 5: Conditional Path, Mostly Good Evidence With One Red Flag

### Setup State

Record a sanction against:

```text
0x5000000000000000000000000000000000000005
```

### Calls

```python
record_sanction(
  "0x5000000000000000000000000000000000000005",
  "Founder misrepresented project runway and ignored disclosure obligations",
  "https://example.com/original-disclosure-failure",
  3,
  1710000000
)
```

After cooldown:

```python
petition_for_redemption(
  5,
  [
    "https://example.com/new-transparent-monthly-updates",
    "https://example.com/third-party-audit-positive",
    "https://example.com/recent-unexplained-token-transfer-red-flag"
  ],
  "https://etherscan.io/address/0x5000000000000000000000000000000000000005",
  1727000000
)
```

### Expected Verdict

```text
CONDITIONAL_REDEMPTION
```

### Why

The evidence includes sustained positive transparency, but one unresolved red flag should prevent full redemption. The address should be removed from the active blacklist but remain visibly conditional.

## Test 6: Severity Edge, Irrecoverable Harm

### Setup State

Record a high-severity sanction against:

```text
0x6000000000000000000000000000000000000006
```

### Calls

```python
record_sanction(
  "0x6000000000000000000000000000000000000006",
  "Theft greater than $1M with no restitution to victims",
  "https://example.com/original-million-dollar-theft-report",
  5,
  1710000000
)
```

After cooldown:

```python
petition_for_redemption(
  6,
  [
    "https://example.com/recent-open-source-contributions",
    "https://example.com/friendly-community-testimonials",
    "https://example.com/no-restitution-yet-statement"
  ],
  "https://etherscan.io/address/0x6000000000000000000000000000000000000006",
  1742000000
)
```

### Expected Verdict

```text
DENIED
```

or:

```text
DENIED_WITH_PATH
```

### Why

Even strong recent behavior should not overcome severe unrepaired harm by itself. The severity discount and restitution scores should remain low until victims are materially repaired.

## Test 7: Premature Petition Rejection

### Setup State

Use any newly recorded sanction with `sanctioned_at = 1710000000`.

### Call

```python
petition_for_redemption(
  1,
  [
    "https://example.com/strong-evidence-but-too-early"
  ],
  "https://etherscan.io/address/0x1000000000000000000000000000000000000001",
  1710000100
)
```

### Expected Result

```text
Cooldown has not elapsed
```

### Why

Default cooldown is 180 days, so a petition 100 seconds later must fail before any AI review runs.

## Test 8: Issuer Appeal After Redemption

### Setup State

Use a sanction whose latest petition returned:

```text
REDEEMED
```

or:

```text
CONDITIONAL_REDEMPTION
```

### Call

```python
appeal_verdict(
  1,
  "The issuer believes the AI ignored unresolved victim claims and over-weighted recent public relations activity.",
  1742100000
)
```

### Expected Verdict

The appeal returns a JSON object with a new verdict. If the appeal evidence exposes unresolved harm, expect:

```text
DENIED_WITH_PATH
```

or:

```text
DENIED
```

### Why

Appeal mode applies stricter scrutiny and can move the sanction back into `PETITION_DENIED` if the re-evaluation score falls below the redemption threshold.

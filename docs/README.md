# ChronoVault

ChronoVault is an on-chain "Parole Officer" for Web3 reputation systems. It lets issuers record sanctions without erasing history, then lets an offender or advocate petition for redemption after a cooldown period.

The protocol is built for GenLayer because the core judgment cannot be expressed as ordinary deterministic Solidity logic. Redemption requires reading public evidence, weighing behavioral patterns, checking restitution, and making a subjective but transparent moral-risk assessment.

## What ChronoVault Solves

Blockchains are perfect-memory machines. That is useful for accountability, but brutal for redemption. A blacklist entry, bad-actor list, or reputation hit can follow a person forever even if they make amends and demonstrably change.

ChronoVault keeps the historical record intact while changing the active label:

- `ACTIVE`: the address is currently sanctioned.
- `REDEEMED`: the sanction remains visible, but the active blacklist is lifted.
- `CONDITIONAL`: the active blacklist is lifted, but the address remains flagged for re-evaluation.
- `PETITION_DENIED`: the petition failed and the sanction remains active.

History is never erased. Redemption is a visible stamp, not deletion.

## Use Cases

- DAO membership reinstatement.
- Lending protocol credit rehabilitation.
- Social graph reputation reset.
- Post-rug-pull founder redemption after restitution.
- Contributor blacklist appeals in open-source DAOs.

## Repository Layout

```text
contracts/
  chronovault.py
  storage_test.py
prompts/
  parole_officer_prompt.md
docs/
  ARCHITECTURE.md
  DEPLOY.md
  README.md
tests/
  manual_test_cases.md
```

## Core Flow

1. An authorized issuer records a sanction with `record_sanction`.
2. The offender remains actively flagged through the cooldown window.
3. After cooldown, anyone may call `petition_for_redemption` with supporting evidence URLs and a chain history URL.
4. The contract renders the original and current evidence using GenLayer nondeterministic web reads.
5. The AI Parole Officer scores five dimensions:
   - Behavioral change.
   - Restitution.
   - Consistency.
   - Severity discount.
   - Recidivism risk.
6. The contract recomputes the final score with integer math and maps it to a verdict.
7. The verdict, scores, cited evidence, and reasoning are stored permanently in the sanction history.

## Contract API

Issuer and config:

```python
set_issuer_authority(issuer: Address, allowed: bool) -> str
configure_vault(key: str, value: str) -> str
get_config(key: str) -> str
is_issuer(address: Address) -> bool
```

Sanctions:

```python
record_sanction(
    offender_address: Address,
    reason: str,
    evidence_url: str,
    severity: u8,
    timestamp: u256
) -> u256
```

Petitions:

```python
petition_for_redemption(
    sanction_id: u256,
    supporting_urls: DynArray[str],
    chain_history_url: str,
    petitioned_at: u256
) -> str
```

Appeals:

```python
appeal_verdict(
    sanction_id: u256,
    appeal_reason: str,
    appealed_at: u256
) -> str
```

Lookup:

```python
check_address_status(address: Address) -> str
get_sanction(sanction_id: u256) -> str
get_sanction_history(address: Address) -> str
get_redemption_verdict(sanction_id: u256) -> str
```

## Notes For Studio

Deploy `contracts/storage_test.py` before deploying the full contract. It verifies that Studio is using the correct GenLayer version header and dependency.

The main contract follows the Studio constraints from the project brief:

- Mandatory `# v0.2.16` header.
- Mandatory `py-genlayer` dependency header.
- Main class named exactly `Contract`.
- Storage collections declared as `TreeMap` or `DynArray`.
- Complex records stored as JSON strings.
- No `float` public signature types.
- All `gl.nondet.*` calls wrapped by `gl.vm.run_nondet_unsafe`.

## Current Implementation Notes

`address_active_sanctions` and `address_redeemed_sanctions` are append-only indexes. Public lookup derives the current status from the canonical JSON sanction records, so redeemed sanctions can remain present in the active index without being treated as active.

Timestamps are caller-supplied Unix seconds. This avoids relying on a Studio clock API and makes manual tests easier to reproduce.

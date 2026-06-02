# ChronoVault

ChronoVault is a GenLayer-powered redemption protocol that lets sanctioned Web3 addresses petition an AI Parole Officer for transparent, evidence-based rehabilitation.

The application connects to the deployed ChronoVault Intelligent Contract on GenLayer StudioNet:

```text
0xB29bfB945A8B32e00fC4125DB7AF78e2c1385A3C
```

## What It Does

ChronoVault preserves sanction history while allowing a person or advocate to request redemption after a cooldown period. The GenLayer contract renders public evidence URLs, asks an AI Parole Officer to evaluate behavioral change, restitution, consistency, severity, and recidivism risk, then stores the resulting verdict on-chain.

## App Features

- Public address status lookup.
- Sanction history and latest verdict reads.
- Issuer-only sanction recording.
- Redemption petition submission with supporting evidence URLs.
- Issuer appeal flow for redemption verdicts.

## Local Development

```bash
npm install
npm run dev
```

Copy `.env.example` to `.env.local` if you need to change the contract address or GenLayer network.

## Contract

The GenLayer Intelligent Contract source lives in:

```text
contracts/chronovault.py
```

Deployment and manual test docs are in:

```text
docs/DEPLOY.md
tests/manual_test_cases.md
```

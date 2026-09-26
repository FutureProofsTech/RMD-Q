# UQ Specification v0.1 (DRAFT — research prototype, NOT a standard)

Status: draft for internal review. Nothing here is standardized, recommended
for use, or security-claimed beyond what Section 06 states explicitly.
Every claim carries its evidence pointer; every gap is listed in 07.

## Layout

- `01-notation.md` — symbols, encodings, domains.
- `02-problem.md` — the RMD-Q assumption (formal statement + planted distribution).
- `03-parameters.md` — frozen parameter sets with per-column rationale.
- `04-kem.md` — key generation, encapsulation, decapsulation (FO-KEM).
- `05-signature.md` — signing and verification (Fiat-Shamir v1, toy status).
- `06-security.md` — claims made here, and claims explicitly NOT made.
- `07-evidence.md` — gap table: each claim mapped to evidence and status.

## Conformance language

MUST / SHALL denote requirements for an implementation to match the KATs in
`../tests/`. Security properties are stated as CONJECTURES with analysis
status, never as guarantees. "Proven" in this spec means "mechanically
checked by the cited test", nothing more.

## Version history

- v0.1 (2026-09-25): first consolidated draft. KEM at n=256/q=3329/k=2 with
  NTT + CBD + FO, fully cross-checked C/Python. Signature v1 toy-only
  (n=16). Planted keygen v2 specified (analysis in ../docs/07).

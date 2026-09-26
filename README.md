# RMD-Q: Restricted Module Decoding with Quadratic Constraint

> **Status: research prototype — NOT for production.** The underlying
> assumption is conjectured and under active kill-phase cryptanalysis.
> No NIST security category is claimed. See [Security posture](#security-posture).

A new post-quantum hardness assumption coupling a noisy module-lattice
relation with a multivariate-quadratic constraint over the same secret —
plus a key-encapsulation mechanism and a signature scheme built from it,
with independently cross-checked C and Python implementations.

Breaking an instance needs a lattice decoder **and** an MQ solver together;
neither alone suffices. One assumption, two primitives, one shared
lightweight codebase (crypto core ≈ 3.9 KB).

## Highlights

| Area | Result |
|------|--------|
| Primitive | KEM (FO transform, implicit rejection) + Fiat-Shamir signatures |
| Ring | `(n,q) = (256,3329)` — the standard lattice ring (NTT reuse, comparability) |
| Speed (host x86-64) | NTT multiply **12.1×**, matrix-vector **13.5×** over schoolbook; full KEM ≈ 0.25 ms; constant-time twins at 1.04–1.17× |
| Sizes (k=2) | pk ≈ 0.8 KB, ct ≈ 0.75 KB (800 B compressed), sig ≈ 1.7–2.0 KB |
| Failures | Exact distributions: 2⁻⁹¹⁰ uncompressed, 2⁻²³⁵ at Kyber-style (10,4); 200k C trials, 0 failures |
| Estimates | Dual-BKZ model validates within 3 bits on ML-KEM-512; ours ~5–7 bits under same-N reference *in-model* |
| Kill-phase | Toy instances fall (brute force, MITM, LLL, Gröbner, msolve); n=32 Gröbner-Basis OOMs at 114 GB on 16 cores |
| Hygiene | ASan/UBSan/valgrind clean, `-Werror` + analyzer silent, Cortex-M4 cross-compile clean |

Details with provenance: [`docs/results/`](docs/results/).

## Repository layout

| Path | Contents |
|------|----------|
| `c/` | Portable C90 implementation (ring, NTT, SHAKE, KEM, tests, benchmarks) |
| `ref/` | Independent Python reference + analysis/attack scripts |
| `tests/` | Known-answer tests (KATs) shared by both implementations |
| `spec/` | v0.1 specification (notation, assumption, parameters, algorithms, claims, evidence gaps) |
| `docs/` | Design notes, audits, and [`docs/results/`](docs/results/) per-topic result documents |
| `paper/` | ePrint submission ([paper.pdf](paper/paper.pdf)), [whitepaper](paper/whitepaper.pdf), [yellowpaper](paper/yellowpaper.pdf) |

## Quick start

Requirements: `gcc`, `python3` (3.10+), `make`. Optional: `arm-none-eabi-gcc`, `valgrind`, `msolve`, `fpylll`, `pdflatex`.

```bash
# Full verification: KAT regen + all C builds/tests + Python suites
bash run_all.sh

# C tests only (default, constant-time, and hardened-only builds)
make -C c test && make -C c ct-test && make -C c no-legacy-test

# Benchmarks and static analysis
./c/bench
make -C c timing-smoke   # objdump check: no sign-jumps in CT paths
make -C c m4-check        # Cortex-M4 cross-compile + sizes
make -C c strict analyze  # -Wconversion -Wpedantic, GCC analyzer
```

## Security posture

- The RMD-Q and planted-MQ assumptions are **conjectures** with model-level support — see [`spec/06-security.md`](spec/06-security.md) for claims made *and explicitly not made*.
- Every attack tried at toy scale either broke the toy (proving the methodology bites) or stalled with documented scaling — see [`docs/results/cryptanalysis.md`](docs/results/cryptanalysis.md).
- `spec/07-evidence.md` maps each claim to evidence and blockers, including a review guide for attackers.

## Documentation map

- Start here for vision and design: [whitepaper](paper/whitepaper.pdf)
- Start here for exactness: [yellowpaper](paper/yellowpaper.pdf) · [`spec/`](spec/)
- Results by topic: [`docs/results/`](docs/results/)
- ePrint submission: [paper.pdf](paper/paper.pdf) (see repo history for submission notes)

## Citation

```bibtex
@misc{rmdq2026,
  author = {nul0 (Future Proofs Tech)},
  title  = {RMD-Q: Restricted Module Decoding with Quadratic Constraint},
  year   = {2026},
  note   = {v0.1 research report, futureproofs@proton.me}
}
```

## License

[GPLv3](LICENSE) — © 2026 nul0 (Future Proofs Tech). Free software:
share and modify, with source and the same freedoms passed on.

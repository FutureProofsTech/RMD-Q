# ePrint submission pack for the RMD-Q report

PDF: `paper/paper.pdf` (rebuild: `cd paper && pdflatex paper.tex` twice).
Source: `paper/paper.tex` + `paper/sec-*.tex` (include sources in revision
uploads; ePrint keeps all versions permanently).

## Suggested form values

- Title: `RMD-Q: Restricted Module Decoding with Quadratic Constraint --- A New Post-Quantum Assumption with Lightweight KEM and Signature Constructions, Analysis, and Verified Prototype`
  (renders MathJax safely; no HTML entities)
- Authors: nul0 (Future Proofs Tech) `<futureproofs@proton.me>` (set in
  `paper.tex`; at least one email present as required).
- Abstract: copy from the paper abstract (plain text, MathJax `$...$` math
  only; strip `\emph{}`, `\cite{}`, `---` is fine as UTF-8).
- Category: Public-key cryptography
- Keywords (<=40 chars each): post-quantum cryptography, module lattices,
  multivariate cryptography, key encapsulation, digital signatures
- Publication: Published nowhere else
- License: see note below (repo is GPLv3; ePrint form is CC-only)

## License note (important)

The repository is licensed GPLv3 (`LICENSE`). The ePrint submission form
only offers Creative Commons licenses (CC BY, BY-SA, BY-NC, BY-NC-SA,
BY-NC-ND, CC0) — GPLv3 is not selectable. Before submitting, decide:
dual-license the paper text (e.g. CC BY-NC-SA, closest to the repo's
non-commercial intent), or contact the editors. Do not submit without
resolving this; the grant is irrevocable.

## Pre-submit checks (all done 2026-09-25 except license decision)

- [x] PDF is A4, builds warning-free (`pdflatex`, 0 errors, refs resolved)
- [x] Email address present in PDF (futureproofs@proton.me)
- [x] No colored link boxes (`hidelinks`); no TODO/color markers in source
- [x] Abstract >= 64 chars, UTF-8 clean
- [x] All paper numbers trace to repo artifacts (`run_all.sh` green)
- [x] Author name + email filled in (nul0, Future Proofs Tech)
- [ ] License chosen at submit time (irrevocable once submitted)
- [ ] Note: withdrawn papers cannot be resurrected; revisions stay public

## Reviewer honesty checklist (what to double-check before submit)

1. The planted-MQ uniformity argument (Sec 3.1) has no proof, only stats.
2. The 20-bit N=768 estimator optimism is stated but unexplained.
3. No ROM/QROM proof sketches exist anywhere (stated in Sec 7).
4. Signature is toy-only; title says "Constructions" (plural) — fair, but
   consider foregrounding KEM-first if reviewers push back.

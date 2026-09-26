# SOUNDNESS + Challenge (v0 — read before use)

## What is proved vs assumed

* Proved (by execution): toy KeyGen outputs `P(s)=0`; toy encrypt/decrypt runs; toy TOY-16 breaks in 172 brute-force tries (see `ref/break_toy.py` output); estimator gives `17.2 bits` brute / `8.6` Grover for TOY-16, `708 bits` for prod sketch.
* Assumed (NOT proved): Search-RMD-Q hardness for `n>=64`; Decision-RMD-Q pseudorandomness; FO/Fiat-Shamir sketches preserve IND-CCA2/SUF-CMA with new `P` check; Grover-only quantum speedup; no structural trapdoor in sparse `P`.
* Gaps: no BKZ/Groebner run on MID-64 yet; no constant-time; no side-channel; Python RNG uses `os.urandom` + SHAKE expand (not SP 800-90 validated); no formal reduction.

## Challenge instances

* `TOY-16 (n=16,q=17,k=1)`: broken — reference break in `ref/break_toy.py`.
* `TOY-32 (n=32,q=97)`: open — expected brute `~2^29`, should fall to MITM + LLL in <1h. Try it.
* `MID-64 (n=64,q=3329,k=2)`: open — target for BKZ-20 + Gröbner. If it falls faster than `2^80`, revise problem.

## Rules for next steps

1. Do not deploy v0. Do not claim Cat levels.
2. Break MID-64 before freezing any prod params.
3. Any tweak to `q,k,eta,w,t,m` requires re-running `test_toy.py + break_toy.py + attack_estimate.py`.
4. Production C backend deferred until problem survives 3-month red-team.

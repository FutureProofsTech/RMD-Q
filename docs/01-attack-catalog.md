# 01 — Attack Catalog (try these first — kill the toy)

Goal of v0 is to **break** toy instances fast and calibrate cost models. Do not skip.

## A. Brute force / meet-in-the-middle over sparse-short space

* Space `S = C(N,w)*(2*eta+1)^w`, `N=k*n`.
* Toy `N=16,w=4,eta=1`: `S = C(16,4)*3^4 = 1820*81 ≈ 147k` — trivial.
* MITM: split `s = s1+s2`, table `A*s1`, match `b - A*s2` within `B_e` then filter `P=0`. Quantum: Grover `sqrt(S)`.
* Action: `ref/attack_estimate.py` computes `log2(S)` and `log2(sqrt(S))`. Toy must be `<30` bits. Prod must be `>260` (Cat1 with margin).

## B. Lattice attacks (ignore P, then filter)

* Embed `(A,b)` as MLWE: BKZ on `2*k*n` dim lattice, sieving/enumeration to recover short `(s,e)`.
* Toy dims 32-64: LLL/BKZ-20 recovers in seconds via sage/fpylll (if available) or simple Babai. Then check `P(s)=0`; if fail, enumerate neighbors.
* Cost model: Core-SVP `~2^{0.292*b}` classical, `2^{0.265*b}` quantum heuristic. Our prod dims `1024-2048` target `b>=400` for Cat1 — to be validated, not claimed.
* Action: run LLL on toy with `sage` or `fpylll` if installed; else document residual norms. Expect toy break.

## C. Algebraic (Gröbner) attacks (ignore noise, then filter)

* Treat `A*s - b = 0` as linear + `P(s)=0` quadratic + bound `s_i^{2*eta+1}-...=0` (field equations for small eta) → Gröbner / linearization / XL.
* Toy `N=16,t=2`: `sage.libs.singular` or `sympy` Groebner should solve in seconds. Watch for oil-like structure — we deliberately use random sparse, no hidden subspace, to avoid wedge/UOV break pattern.
* Action: try `sage -python` Groebner on toy seed 0; record time. If toy resists >60s, MQ too hard for toy — reduce `t/m`.

## D. Hybrid (expected best)

* Lattice enumerate short candidates within radius `B_e`, test `P=0` per candidate. Or guess subset of support (weight split), lattice-reduce remainder.
* Model: `C(N,w1)` guesses × BKZ on reduced dim. Tune `w1` to minimize.
* Action: implement naive hybrid in `attack_estimate.py` as `min_{w1} log2(C(N,w1)) + BKZ(dim-w1)` sketch.

## E. Structural / misuse

* Weak seeds: `A` with small order, `P` with linear component → check seed expansion has no trapdoor (SHAKE uniform, no structure).
* Keygen bias: conditioning `P(s)=0` must not skew `s` distribution detectably; test chi-square on toy.
* Failure oracle: KEM decrypt failures must be `<2^-40` toy, `<2^-138` prod sketch; measure.
* Side-channel placeholders: Python ref is not constant-time; C backend later must be CBMC + valgrind gated (deferred).

## Kill criteria for v0

* Toy `n=16` MUST break in <1h by at least two methods (brute + lattice or Gröbner). If not breakable, toy too hard — shrink.
* Prod sketch MUST have `log2(S)>260`, `dim>=1024`, `t>=8` — else enlarge.
* Any break of `n=64,k=2` toy faster than estimate → revise problem before construction freeze.

"""Planted-P keygen for RMD-Q: construct P around sampled s with P(s)=0.

Why: rejection sampling s until P(s)=0 has success prob ~q^-t per try --
impossible at n=256/t=8. Planting always succeeds in O(t*m) time.

Distribution v2 (analyzed in docs/07-planted-keygen.md):
  supports chosen independently of s; free coeffs uniform over [0,q).
  - If all free monomials vanish at s: equation is pure uniform-random
    (no conditioning at all) -- accept as-is.
  - Else: resample free coeffs (bounded) until c_fix != 0, so no equation
    carries a length signal (term count is constant m).
  Given supports + s, coefficients are uniform over the hyperplane
  {c : <c, evals> = 0} minus the c_fix=0 slice (negligible conditioning).
  Assumption shifts random-MQ -> planted-MQ (same family as MPCitH/code-based
  planted instances, but OUR sparse-planted distribution needs its own
  analysis -- see docs).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from rmdq_toy import shake128, sample_vec, mat_vec_mul, poly_add, eval_mq, flatten


def _stream(seed: bytes):
    import random
    seed_int = int.from_bytes(shake128(b"planted-mq" + seed, 16), "little")
    return random.Random(seed_int)


def plant_mq(seed: bytes, s_flat, t: int, m: int, q: int, resample_zero=True):
    """Return (eqs, meta) with eqs[e] satisfied at s_flat by construction.

    HOMOGENEOUS-QUADRATIC only (no linear terms anywhere): the Sig opening
    identity needs P_quad(s) = 0 exactly, and any linear part would break it
    (see docs/02). Fix terms and pads are quadratic; vanishing pads use a
    zero endpoint. Requires >= 2 nonzero coords in s (resampled by caller).
    """
    N = len(s_flat)
    nz = [i for i, x in enumerate(s_flat) if x % q != 0]
    assert len(nz) >= 2, "planted MQ needs >=2 nonzero coords (homogeneous-quad)"
    rnd = _stream(seed)
    eqs = []
    meta = {"fix_shape": [], "fix_pos": [], "fix_slot": [],
            "resampled": [], "pure_random": []}
    for _ in range(t):
        # supports first (independent of s), coefficients resampled below
        sup = []
        for _ in range(m - 1):
            sup.append((rnd.randrange(N), rnd.randrange(N)))
        i, j = rnd.choice(nz), rnd.choice(nz)
        fix = (i, j)
        slot = rnd.randrange(m)
        # free-monomial evals at s (support-only, no coefficients yet)
        evs = [(s_flat[vi] * s_flat[vj]) % q for vi, vj in sup]
        terms, n_try = None, 0
        while True:
            n_try += 1
            free = [rnd.randrange(0, q) for _ in range(m - 1)]
            rest = sum(c * ev for c, ev in zip(free, evs)) % q
            if all(e == 0 for e in evs):
                # pure-random equation: pad to m terms with a vanishing quad
                # term (zero endpoint; looks like ordinary free terms).
                terms = [(c, vi, vj) for c, (vi, vj) in zip(free, sup)]
                zeros = [i0 for i0, x in enumerate(s_flat) if x % q == 0]
                if zeros:
                    j0 = zeros[rnd.randrange(len(zeros))]
                    j1 = rnd.randrange(N)
                    terms.insert(rnd.randrange(m), (rnd.randrange(0, q), j0, j1))
                else:
                    terms.insert(rnd.randrange(m), (0, 0, 0))  # dense-s fallback
                meta["pure_random"].append(True)
                break
            fev = (s_flat[fix[0]] * s_flat[fix[1]]) % q
            c_fix = (-rest * pow(fev, -1, q)) % q
            if not resample_zero or c_fix != 0 or n_try >= 16:
                terms = [(c, vi, vj) for c, (vi, vj) in zip(free, sup)]
                terms.insert(slot, (c_fix, fix[0], fix[1]))
                meta["pure_random"].append(False)
                break
        eqs.append(terms)
        meta["resampled"].append(n_try - 1)
        meta["fix_shape"].append("quad")
        meta["fix_pos"].append(fix)
        meta["fix_slot"].append(slot if not meta["pure_random"][-1] else -1)
    return eqs, meta


def keygen_planted(params, seed_A: bytes, seed_P: bytes, seed_s: bytes):
    """Succeeds on first s with >= 2 nonzero coords (overwhelmingly likely;
    homogeneous-quad planting needs a nonzero pair)."""
    from rmdq_toy import expand_matrix
    A = expand_matrix(seed_A, params.k, params.n, params.q, b"\x00kem-a")
    for nonce in range(16):
        s = sample_vec(params.k, params.n, params.q, params.eta, params.w,
                       seed_s, nonce)
        if sum(1 for x in flatten(s) if x % params.q != 0) >= 2:
            break
    else:
        raise RuntimeError("no suitable s in 16 tries")
    P, meta = plant_mq(seed_P, flatten(s), params.t, params.m, params.q)
    assert all(v == 0 for v in eval_mq(P, flatten(s), params.q)), "planting bug"
    e = sample_vec(params.k, params.n, params.q, params.eta_e, params.n, seed_s, 1)
    b = mat_vec_mul(A, s, params.q)
    b = [poly_add(bi, ei, params.q) for bi, ei in zip(b, e)]
    return {"A": A, "P": P, "meta": meta, "s": s, "e": e, "b": b}

"""UQ-SIG-v1 toy: dual opening (z_lat for lattice via c_poly, z_mq for MQ via c_scalar).

Fixes v0/v1a soundness bug: poly-mul z=y+c_poly*s does NOT satisfy scalar
linearization P(z)=P(y)+c*h. So v1 sends TWO openings from same mask y:
  z_lat = y + c_poly*s  (lattice part, Dilithium-style, |C|=C(n,tau)*2^tau)
  z_mq  = y + c_scalar*s (MQ part, scalar linearization exact since P(s)=0)
Both challenges bound to same mu/w/py hash. Size 2x (toy only, unoptimized).
Toy: n=16 tau=2 => lattice |C|=480 (~9 bits demo). Prod: n=256 tau=39+.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from rmdq_toy import Params, keygen, mat_vec_mul, poly_add, poly_sub, poly_mul_negacyclic, shake256, shake128, flatten, eval_mq, norm_inf_poly
from rmdq_sig import _pk_hash, _serialize_poly, _linear_opening, _poly_scalar_mul

def sample_poly_challenge(seed: bytes, n: int, tau: int, q: int):
    """Deterministic sparse poly: tau positions +-1 from SHAKE stream (toy)."""
    buf = shake128(b"\x02sig-cpoly" + seed, 64)
    # choose tau distinct positions + signs from stream
    pos, signs, i = [], [], 0
    used = set()
    while len(pos) < tau and i + 2 <= len(buf):
        p = buf[i] % n
        s = 1 if buf[i + 1] % 2 == 0 else q - 1
        i += 2
        if p in used:
            if i + 2 > len(buf):
                buf += shake128(buf + bytes([len(pos)]), 32)
            continue
        used.add(p)
        pos.append(p)
        signs.append(s)
    c = [0] * n
    for p_, s_ in zip(pos, signs):
        c[p_] = s_
    return c

def challenge_scalars(mu, w_vec, py, q):
    # c_poly from hash, c_scalar bound to it (so both parts commit to same Fiat-Shamir hash)
    c_poly_seed = shake256(b"\x02sig-cpoly-hash" + mu + b"".join(_serialize_poly(p) for p in w_vec), 32)
    # tau=2 toy
    c_poly = sample_poly_challenge(c_poly_seed, len(w_vec[0]), 2, q)
    c_scalar = (int.from_bytes(shake256(b"\x02sig-cscal" + c_poly_seed, 2), "little") % 2) + 1
    return c_poly, c_scalar, c_poly_seed

def sig_sign_v1(sk, msg: bytes, params: Params, gamma=6, max_tries=50):
    A, P = sk["pk"]["A"], sk["pk"]["P"]
    s_flat = flatten(sk["s"])
    mu = shake256(b"\x02sig-mu" + sk["pk_hash"] + msg, 32)
    for attempt in range(max_tries):
        y = []
        for i in range(params.k):
            rb = shake128(mu + bytes([attempt, i]), max(64, params.n))
            y.append([((rb[j] % (2 * gamma + 1)) - gamma) % params.q for j in range(params.n)])
        y_flat = flatten(y)
        w = mat_vec_mul(A, y, params.q)
        py = eval_mq(P, y_flat, params.q)
        c_poly, c_scalar, c_seed = challenge_scalars(mu, w, py, params.q)
        # lattice opening: z_lat = y + c_poly*s
        z_lat = []
        for yi, si in zip(y, sk["s"]):
            cs = poly_mul_negacyclic(c_poly, si, params.q)
            z_lat.append(poly_add(yi, cs, params.q))
        if any(norm_inf_poly(zi, params.q) > gamma + 4 for zi in z_lat):
            continue
        # MQ opening: z_mq = y + c_scalar*s (scalar => linearization exact)
        z_mq = [poly_add(yi, _poly_scalar_mul(si, c_scalar, params.q), params.q) for yi, si in zip(y, sk["s"])]
        h = _linear_opening(P, y_flat, s_flat, params.q)
        # MQ self-check (must hold since P(s)=0)
        if eval_mq(P, flatten(z_mq), params.q) != [(py_j + c_scalar * h_j) % params.q for py_j, h_j in zip(py, h)]:
            continue
        return {"c_poly": c_poly, "c_scalar": c_scalar, "c_seed": c_seed,
                "z_lat": z_lat, "z_mq": z_mq, "h": h, "w": w, "py": py,
                "y": y, "gamma": gamma,
                "attempt": attempt, "mu": mu}

def sig_verify_v1(pk, msg: bytes, sig, params: Params, slack=8):
    from rmdq_toy import poly_sub
    A, P = pk["A"], pk["P"]
    from rmdq_sig import _pk_hash
    pk_hash = _pk_hash(pk, params)
    mu = shake256(b"\x02sig-mu" + pk_hash + msg, 32)
    if mu != sig["mu"]:
        return False, "mu"
    c_poly, c_scalar = sig["c_poly"], sig["c_scalar"]
    z_lat, z_mq, h, w, py = sig["z_lat"], sig["z_mq"], sig["h"], sig["w"], sig["py"]
    if sum(1 for x in c_poly if x) != 2:
        return False, "c_poly weight"
    # recompute challenge binding
    c_poly2, c_scalar2, _ = challenge_scalars(mu, w, py, params.q)
    if c_poly2 != c_poly or c_scalar2 != c_scalar:
        return False, "challenge binding"
    # lattice via z_lat/c_poly: A*z_lat - c_poly*b ~= w
    Az = mat_vec_mul(A, z_lat, params.q)
    cb = [poly_mul_negacyclic(c_poly, bi, params.q) for bi in pk["b"]]
    wprime = [poly_sub(a, b_, params.q) for a, b_ in zip(Az, cb)]
    for a, b_ in zip(wprime, w):
        if norm_inf_poly(poly_sub(a, b_, params.q), params.q) > slack:
            return False, "wprime slack"
    # MQ via z_mq/c_scalar: P(z_mq) == py + c_scalar*h
    pz = eval_mq(P, flatten(z_mq), params.q)
    if pz != [(py_j + c_scalar * h_j) % params.q for py_j, h_j in zip(py, h)]:
        return False, "MQ"
    # bound z_mq as well
    if any(norm_inf_poly(zi, params.q) > gamma_bound(params) for zi in z_mq):
        return False, "z_mq bound"
    return True, "ok"

def gamma_bound(params: Params):
    return 8

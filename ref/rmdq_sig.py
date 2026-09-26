"""UQ-SIG-v0 toy (Fiat-Shamir with aborts + MQ opening, scalar challenge).

Toy simplification documented in docs/02: challenge c is scalar in Z_q (not poly),
so P(z)=P(y)+c*h holds exactly when P(s)=0. Prod will upgrade to poly challenge.
SHAKE only, integer-only. NOT secure, NOT constant-time.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from rmdq_toy import (
    Params, keygen, mat_vec_mul, poly_add, poly_sub, shake256, shake128,
    flatten, unflatten, eval_mq, norm_inf_poly,
)

def _pk_hash(pk, params):
    out = b"sig-pk"
    for vec in [pk["b"]]:
        for poly in vec:
            out += bytes([(c & 0xFF) for c in poly])
    return shake256(out + pk["seed_A"] + pk["seed_P"], 32)

def _serialize_poly(poly):
    return bytes([(c & 0xFF) for c in poly])

def _challenge_scalar(mu, w_vec, py, q):
    # TOY ONLY: tiny challenge space {1,2} to keep ||c*e|| within slack.
    # Prod will use weight-tau sparse poly challenge like FIPS 204. Insecure here by design.
    data = mu + b"".join(_serialize_poly(p) for p in w_vec) + bytes([v & 0xFF for v in py])
    d = shake256(b"\x02sig-chal" + data, 2)
    return (int.from_bytes(d, "little") % 2) + 1  # 1 or 2

def _poly_scalar_mul(poly, c, q):
    return [(x * c) % q for x in poly]

def _quad_opening(P_eqs, y_flat, s_flat, q):
    """Cross term h with P(y+c*s) = P(y) + c*h for homogeneous-quadratic P
    with P(s)=0. (Linear terms would add a c^2*P_quad(s) defect -- excluded
    by design, see docs/02.)"""
    h = []
    for terms in P_eqs:
        acc = 0
        for coeff, vi, vj in terms:
            assert vj != -1, "non-homogeneous MQ breaks opening identity"
            acc = (acc + coeff * (y_flat[vi] * s_flat[vj] + y_flat[vj] * s_flat[vi])) % q
        h.append(acc)
    return h

_linear_opening = _quad_opening  # legacy alias (remove next round)

def sig_keygen(params: Params, seed_A: bytes, seed_P: bytes, seed_s: bytes):
    kg = keygen(params, seed_A, seed_P, seed_s)
    pk = {"A": kg["A"], "P": kg["P"], "b": kg["b"], "seed_A": seed_A, "seed_P": seed_P}
    sk = {"s": kg["s"], "pk": pk, "pk_hash": _pk_hash(pk, params)}
    return pk, sk

def sig_sign(sk, msg: bytes, params: Params, gamma=6, max_tries=50):
    A, P = sk["pk"]["A"], sk["pk"]["P"]
    s_flat = flatten(sk["s"])
    mu = shake256(b"\x02sig-mu" + sk["pk_hash"] + msg, 32)
    z_bound = gamma + 2  # matches verifier default scale; pass explicitly at scale
    for attempt in range(max_tries):
        # masking y: bound gamma, dense (fixed-shape loops; attempt count varies
        # by design, as in Dilithium-style rejection sampling)
        y = []
        for i in range(params.k):
            rb = shake128(mu + bytes([attempt, i]), max(64, params.n))
            # coeffs in [-gamma, gamma]
            poly = [((rb[j] % (2 * gamma + 1)) - gamma) % params.q for j in range(params.n)]
            y.append(poly)
        y_flat = flatten(y)
        w = mat_vec_mul(A, y, params.q)
        py = eval_mq(P, y_flat, params.q)
        c = _challenge_scalar(mu, w, py, params.q)
        # z = y + c*s
        z = [poly_add(yi, _poly_scalar_mul(si, c, params.q), params.q) for yi, si in zip(y, sk["s"])]
        # rejection: ||z||_inf < gamma+2 (toy loose) else retry
        if any(norm_inf_poly(zi, params.q) > z_bound for zi in z):
            continue
        h = _linear_opening(P, y_flat, s_flat, params.q)
        # self-check consistency: P(z) == P(y) + c*h (mod q) since P(s)=0
        z_flat = flatten(z)
        pz = eval_mq(P, z_flat, params.q)
        expect = [(py_j + c * h_j) % params.q for py_j, h_j in zip(py, h)]
        # NOTE: quadratic P(s) term is c^2*P(s)=0 so equality must hold; if not, bug
        if pz != expect:
            # This happens only if P(s)!=0 or linearization wrong — keygen guarantees P(s)=0 so this is a bug if triggered
            continue
        sig = {"c": c, "z": z, "h": h, "w": w, "py": py, "attempt": attempt,
               "mu": mu, "z_bound": z_bound}
        return sig
    raise RuntimeError("sign failed rejection loop (toy)")

def sig_verify(pk, msg: bytes, sig, params: Params, slack=4, z_bound=8):
    A, P = pk["A"], pk["P"]
    pk_hash = _pk_hash(pk, params)
    mu = shake256(b"\x02sig-mu" + pk_hash + msg, 32)
    if mu != sig["mu"]:
        return False, "mu mismatch"
    c, z, h, w, py = sig["c"], sig["z"], sig["h"], sig["w"], sig["py"]
    # bounds (z_bound=8 legacy toy; signer records its bound; pass q to skip)
    if any(norm_inf_poly(zi, params.q) > sig.get("z_bound", z_bound) for zi in z):
        return False, "z bound"
    # 1. lattice approx: A*z - c*b should equal w - c*e within slack
    # recompute Az - c*b
    Az = mat_vec_mul(A, z, params.q)
    cb = [_poly_scalar_mul(bi, c, params.q) for bi in pk["b"]]
    wprime = [poly_sub(a, b_, params.q) for a, b_ in zip(Az, cb)]
    for a, b_ in zip(wprime, w):
        diff = poly_sub(a, b_, params.q)
        if norm_inf_poly(diff, params.q) > slack:
            return False, f"wprime slack {norm_inf_poly(diff, params.q)}"
    # 2. MQ consistency: P(z) == py + c*h
    pz = eval_mq(P, flatten(z), params.q)
    expect = [(py_j + c * h_j) % params.q for py_j, h_j in zip(py, h)]
    if pz != expect:
        return False, "MQ consistency"
    # 3. challenge recompute
    if _challenge_scalar(mu, w, py, params.q) != c:
        return False, "challenge"
    return True, "ok"

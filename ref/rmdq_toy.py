"""RMD-Q toy reference (portable Python, FIPS 202 SHAKE only, no float).

Implements docs/00 + docs/02 for tiny params so tests break it fast.
NOT constant-time, NOT production. For correctness + KAT + attack calibration only.
"""
import hashlib
import os

# ---------------- ring utils (naive, toy only) ----------------

def mod_q(x, q):
    return x % q

def poly_add(a, b, q):
    return [(x + y) % q for x, y in zip(a, b)]

def poly_sub(a, b, q):
    return [(x - y) % q for x, y in zip(a, b)]

def poly_mul_negacyclic(a, b, q):
    # R = Z_q[X]/(X^n+1), naive O(n^2) toy
    n = len(a)
    assert len(b) == n
    tmp = [0] * (2 * n)
    for i, ai in enumerate(a):
        if ai == 0:
            continue
        for j, bj in enumerate(b):
            if bj == 0:
                continue
            tmp[i + j] = (tmp[i + j] + ai * bj) % q
    # reduce X^n = -1
    res = tmp[:n]
    for i in range(n, 2 * n):
        res[i - n] = (res[i - n] - tmp[i]) % q
    return res

def mat_vec_mul(A, vec, q):
    # A: k x k polys, vec: k polys -> k polys
    k = len(vec)
    out = [[0] * len(vec[0]) for _ in range(k)]
    for i in range(k):
        acc = [0] * len(vec[0])
        for j in range(k):
            prod = poly_mul_negacyclic(A[i][j], vec[j], q)
            acc = poly_add(acc, prod, q)
        out[i] = acc
    return out

def dot(a_vec, b_vec, q):
    acc = [0] * len(a_vec[0])
    for x, y in zip(a_vec, b_vec):
        acc = poly_add(acc, poly_mul_negacyclic(x, y, q), q)
    return acc

def norm_inf_poly(p, q):
    # centered representative in [-(q-1)/2, (q-1)/2]
    m = 0
    for c in p:
        cc = c if c <= q // 2 else c - q
        m = max(m, abs(cc))
    return m

def weight_poly(p):
    return sum(1 for c in p if c != 0)

# ---------------- SHAKE expansion (FIPS 202 only) ----------------

def shake128(data: bytes, outlen: int) -> bytes:
    return hashlib.shake_128(data).digest(outlen)

def shake256(data: bytes, outlen: int) -> bytes:
    return hashlib.shake_256(data).digest(outlen)

def expand_matrix(seed: bytes, k: int, n: int, q: int, tag: bytes) -> list:
    A = [[None] * k for _ in range(k)]
    for i in range(k):
        for j in range(k):
            # enough bytes for n coeffs < q (simple rej sampling)
            buf = shake128(tag + seed + bytes([i, j]), 4 * n)
            poly = []
            idx = 0
            while len(poly) < n:
                v = int.from_bytes(buf[idx:idx + 2], "little") % q
                # use 2 bytes per coeff, advance; refill if needed (toy simple)
                poly.append(v)
                idx += 2
                if idx + 2 > len(buf):
                    buf += shake128(buf + bytes([len(poly)]), 4 * n)
            A[i][j] = poly
    return A

def expand_mq(seed: bytes, t: int, N: int, m: int, q: int):
    """Sparse HOMOGENEOUS-QUADRATIC MQ system: list of t equations of
    (coeff, var_i, var_j) with var_j always >= 0 (no linear terms).
    Homogeneity is load-bearing: the Sig opening identity
    P(y+c*s) = P(y) + c*h requires P_quad(s) = 0 exactly, which planted/
    rejection keygen guarantees only without linear parts (see docs/02).
    """
    import random
    # deterministic PRNG from SHAKE for reproducibility (not secure RNG, just expand)
    seed_int = int.from_bytes(shake128(b"mq-deterministic" + seed, 16), "little")
    rnd = random.Random(seed_int)
    eqs = []
    for _ in range(t):
        terms = []
        for _ in range(m):
            c = rnd.randrange(1, q)
            vi = rnd.randrange(N)
            vj = rnd.randrange(N)
            terms.append((c, vi, vj))
        eqs.append(terms)
    return eqs

def eval_mq(eqs, s_flat, q):
    out = []
    for terms in eqs:
        acc = 0
        for c, vi, vj in terms:
            if vj == -1:
                acc = (acc + c * s_flat[vi]) % q
            else:
                acc = (acc + c * s_flat[vi] * s_flat[vj]) % q
        out.append(acc)
    return out

def flatten(vec):
    return [c for poly in vec for c in poly]

def unflatten(flat, k, n):
    return [flat[i * n:(i + 1) * n] for i in range(k)]

# ---------------- sampling ----------------

def sample_sparse_poly(n, q, eta, w, rng_bytes):
    # map bytes to coeffs in [-eta, eta] then sparsify to weight w (keep first w nonzeros deterministically for testability is avoided; use rng)
    vals = []
    for i in range(n):
        b = rng_bytes[i] % (2 * eta + 1)
        v = b - eta  # in [-eta, eta]
        vals.append(v % q)
    # sparsify: zero out all but w positions chosen by next bytes
    if weight_poly(vals) > w:
        idxs = list(range(n))
        # deterministic shuffle by rng
        order = sorted(idxs, key=lambda i: rng_bytes[(n + i) % len(rng_bytes)])
        keep = set(order[:w])
        vals = [v if i in keep else 0 for i, v in enumerate(vals)]
    return vals

def _rb_len(n):
    # legacy 64B for n<=32 (existing KATs byte-exact); 2*n bytes beyond
    return 64 if n <= 32 else 2 * n


def compress_poly(poly, d, q):
    """Kyber-style lossy compress to d bits/coeff (exact integer arithmetic)."""
    out = []
    for x in poly:
        out.append((((x % q) << d) + q // 2) // q % (1 << d))
    return out


def decompress_poly(comp, d, q):
    out = []
    for c in comp:
        out.append((c * q + (1 << (d - 1))) // (1 << d) % q)
    return out


def sample_vec(k, n, q, eta, w, seed, nonce):
    vec = []
    for i in range(k):
        rb = shake128(seed + bytes([nonce, i]), _rb_len(n))
        vec.append(sample_sparse_poly(n, q, eta, w, rb))
    return vec


def cbd_poly(buf: bytes, n: int, eta: int, q: int):
    """Centered binomial, Kyber-style fixed-shape sampling (constant-time
    shape: fixed loops, bit ops only). Bit-identical to C rmdq_cbd."""
    out = []
    for i in range(n):
        d = 0
        for j in range(eta):
            b0 = (buf[(2 * i * eta + j) >> 3] >> ((2 * i * eta + j) & 7)) & 1
            b1 = (buf[((2 * i + 1) * eta + j) >> 3] >> (((2 * i + 1) * eta + j) & 7)) & 1
            d += b0 - b1
        out.append(d % q)
    return out


def _cbd_len(n, eta):
    return (n * eta * 2 + 7) // 8


def sample_cbd_vec(k, n, q, eta, seed, nonce):
    vec = []
    for i in range(k):
        rb = shake128(seed + bytes([nonce, i]), _cbd_len(n, eta))
        vec.append(cbd_poly(rb, n, eta, q))
    return vec

# ---------------- keygen / encrypt / decrypt (toy CPA-PKE) ----------------

class Params:
    def __init__(self, n=16, q=17, k=1, eta=1, w=4, eta_e=1, t=2, m=4, du=3, dv=2):
        self.n, self.q, self.k = n, q, k
        self.eta, self.w, self.eta_e = eta, w, eta_e
        self.t, self.m, self.du, self.dv = t, m, du, dv

def keygen(params: Params, seed_A: bytes, seed_P: bytes, seed_s: bytes, max_tries=256,
           cbd_err=False):
    A = expand_matrix(seed_A, params.k, params.n, params.q, b"\x00kem-a")
    N = params.k * params.n
    P = expand_mq(seed_P, params.t, N, params.m, params.q)
    for attempt in range(max_tries):
        s = sample_vec(params.k, params.n, params.q, params.eta, params.w, seed_s, attempt)
        if any(v != 0 for v in eval_mq(P, flatten(s), params.q)):
            continue
        if cbd_err:
            # hardened path: dense CBD error (standard MLWE noise); s stays sparse
            e = sample_cbd_vec(params.k, params.n, params.q, params.eta_e, seed_s,
                               100 + attempt)
        else:
            e = sample_vec(params.k, params.n, params.q, params.eta_e, params.n, seed_s, 100 + attempt)
        b = mat_vec_mul(A, s, params.q)
        b = [poly_add(bi, ei, params.q) for bi, ei in zip(b, e)]
        return {"A": A, "P": P, "s": s, "e": e, "b": b, "attempt": attempt}
    raise RuntimeError("keygen failed: P(s)=0 too rare, reduce t/m")

def encode_msg(msg32: bytes, n: int, q: int):
    # toy: repeat bits across coeffs, scale by q//2
    bits = []
    for byte in msg32:
        for i in range(8):
            bits.append((byte >> i) & 1)
    poly = [(q // 2 if bits[i % len(bits)] else 0) for i in range(n)]
    return poly

def decode_msg(poly, q):
    bits = [1 if (c if c <= q // 2 else c - q) > q // 4 else 0 for c in poly[:32 * 8]]
    # toy n may be <256 bits; just pack available
    out = bytearray(32)
    for i, bit in enumerate(bits):
        out[i // 8] |= (bit << (i % 8))
    return bytes(out[: (len(poly) + 7) // 8])

def encrypt(pk, msg32: bytes, params: Params, seed_r: bytes, cbd=False):
    A, b = pk["A"], pk["b"]
    if cbd:
        # hardened path: dense CBD randomness (fixed-shape sampling)
        r = sample_cbd_vec(params.k, params.n, params.q, params.eta, seed_r, 0)
        e1 = sample_cbd_vec(params.k, params.n, params.q, params.eta_e, seed_r, 1)
        e2 = cbd_poly(shake128(seed_r + b"e2", _cbd_len(params.n, params.eta_e)),
                      params.n, params.eta_e, params.q)
    else:
        r = sample_vec(params.k, params.n, params.q, params.eta, params.w, seed_r, 0)
        e1 = sample_vec(params.k, params.n, params.q, params.eta_e, params.n, seed_r, 1)
        e2 = sample_sparse_poly(params.n, params.q, params.eta_e, params.n,
                                shake128(seed_r + b"e2", _rb_len(params.n)))
    # u = A^T r + e1 (toy symmetric, use A directly since k=1; general transpose below)
    AT = [[A[j][i] for j in range(params.k)] for i in range(params.k)]
    u = mat_vec_mul(AT, r, params.q)
    u = [poly_add(ui, ei, params.q) for ui, ei in zip(u, e1)]
    v = poly_add(dot(b, r, params.q), e2, params.q)
    v = poly_add(v, encode_msg(msg32, params.n, params.q), params.q)
    return {"u": u, "v": v, "r": r}

def decrypt(sk, ct, params: Params):
    s = sk["s"]
    u, v = ct["u"], ct["v"]
    su = dot(s, u, params.q)
    m_poly = poly_sub(v, su, params.q)
    # toy decode: nearest to 0 or q//2
    q = params.q
    bits = []
    for c in m_poly:
        # distance to 0 vs q//2
        d0 = min(c, q - c)
        d1 = abs(c - q // 2)
        bits.append(0 if d0 < d1 else 1)
    return bits, m_poly

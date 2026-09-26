"""UQ-KEM-v0 FO wrapper (toy): IND-CCA2 shape with implicit rejection.

Built on ref/rmdq_toy CPA-PKE. SHAKE only. Toy correctness measured, not claimed secure.
"""
import hashlib
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from rmdq_toy import Params, keygen, encrypt, dot, poly_sub, shake256, flatten

def _pack_ct(u, v, du, dv):
    # canonical compressed wire bytes (lossless packing of compressed coeffs)
    out = b""
    for poly in u:
        out += _pack_poly(poly, du)
    out += _pack_poly(v, dv)
    return out


def _pack_poly(poly, bits):
    acc = accbits = 0
    out = bytearray()
    for c in poly:
        acc |= (c & ((1 << bits) - 1)) << accbits
        accbits += bits
        while accbits >= 8:
            out.append(acc & 0xFF)
            acc >>= 8
            accbits -= 8
    if accbits:
        out.append(acc & 0xFF)
    return bytes(out)


def _pk_bytes(pk, params):
    # canonical serialization for hashing: b polys + seeds lengths (toy, not packed)
    out = b""
    for poly in [p for vec in [pk["b"]] for p in vec]:
        out += bytes([(c & 0xFF) for c in poly])
    return out

def _ct_bytes(ct):
    out = b""
    for vec in [ct["u"]]:
        for poly in vec:
            out += bytes([(c & 0xFF) for c in poly])
    out += bytes([(c & 0xFF) for c in ct["v"]])
    return out

def kem_keygen(params: Params, seed_A: bytes, seed_P: bytes, seed_s: bytes,
               cbd_err=False):
    kg = keygen(params, seed_A, seed_P, seed_s, cbd_err=cbd_err)
    pk = {"A": kg["A"], "P": kg["P"], "b": kg["b"], "seed_A": seed_A, "seed_P": seed_P}
    pk_hash = shake256(_pk_bytes(pk, params) + seed_A + seed_P, 32)
    sigma = shake256(b"implicit-reject" + seed_s, 32)  # secret reject seed
    sk = {"s": kg["s"], "pk": pk, "pk_hash": pk_hash, "sigma": sigma}
    return pk, sk

def kem_encaps(pk, params: Params, m32: bytes = None, cbd=False,
               du=None, dv=None):
    # TOY: message space is n bits (core_len bytes); tail canonicalized to 0x00
    # because toy n=16 cannot carry 32B. Prod n=256 carries 32B exactly.
    # du/dv set: compressed wire format (ct stored/transmitted compressed;
    # KDF binds the compressed bytes, re-encrypt check re-compresses).
    from rmdq_toy import compress_poly
    core = (params.n + 7) // 8
    if m32 is None:
        m32 = os.urandom(32)
    m32 = m32[:core] + b"\x00" * (32 - core)
    pk_hash = shake256(_pk_bytes(pk, params) + pk["seed_A"] + pk["seed_P"], 32)
    coins = shake256(b"\x01kem-coins" + m32 + pk_hash, 32)
    ct = encrypt(pk, m32, params, coins, cbd=cbd)
    if du is not None:
        cu = [compress_poly(p, du, params.q) for p in ct["u"]]
        cv = compress_poly(ct["v"], dv, params.q)
        ct = {"u": cu, "v": cv, "compressed": (du, dv)}
        K = shake256(b"\x01kem-shared" + m32 + _pack_ct(cu, cv, du, dv), 32)
    else:
        K = shake256(b"\x01kem-shared" + m32 + _ct_bytes(ct), 32)
    return K, ct, m32

def kem_decaps(sk, ct, params: Params, cbd=False, du=None, dv=None):
    from rmdq_toy import decrypt, decompress_poly
    pk = sk["pk"]
    if du is not None:
        ctu = [decompress_poly(p, du, params.q) for p in ct["u"]]
        ctv = decompress_poly(ct["v"], dv, params.q)
    else:
        ctu, ctv = ct["u"], ct["v"]
    # CPA decrypt to bit vector then re-encode to bytes for toy (lossy: use hash of poly instead)
    bits, mpoly = decrypt({"s": sk["s"]}, {"u": ctu, "v": ctv}, params)
    # toy: recover m by mapping bits back to bytes (only n bits meaningful)
    m_rec = bytearray(32)
    for i, bit in enumerate(bits):
        if i >= 256:
            break
        m_rec[i // 8] |= (bit << (i % 8))
    m_rec = bytes(m_rec)
    # re-encrypt check (re-compress to compare on the wire format)
    pk_hash = sk["pk_hash"]
    coins = shake256(b"\x01kem-coins" + m_rec + pk_hash, 32)
    ct2 = encrypt(pk, m_rec, params, coins, cbd=cbd)
    if du is not None:
        from rmdq_toy import compress_poly
        ct2 = {"u": [compress_poly(p, du, params.q) for p in ct2["u"]],
               "v": compress_poly(ct2["v"], dv, params.q)}
        if ct2["u"] == ct["u"] and ct2["v"] == ct["v"]:
            return shake256(b"\x01kem-shared" + m_rec +
                            _pack_ct(ct["u"], ct["v"], du, dv), 32), True
        return shake256(b"reject" + sk["sigma"] +
                        _pack_ct(ct["u"], ct["v"], du, dv), 32), False
    if _ct_bytes(ct2) == _ct_bytes(ct):
        return shake256(b"\x01kem-shared" + m_rec + _ct_bytes(ct), 32), True
    return shake256(b"reject" + sk["sigma"] + _ct_bytes(ct), 32), False

"""n=256 q=3329 k=2 KEM KAT for C cross-check (t=0: lattice path only)."""
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from rmdq_toy import Params, flatten
from rmdq_kem import kem_keygen, kem_encaps, kem_decaps

def main():
    p = Params(n=256, q=3329, k=2, eta=2, w=128, eta_e=2, t=0, m=0)
    seed_A, seed_P, seed_S = b"C256-A-000000000", b"C256-P-000000000", b"C256-S-000000000"
    from rmdq_toy import keygen, encrypt
    kg = keygen(p, seed_A, seed_P, seed_S)
    pk = {"A": kg["A"], "P": kg["P"], "b": kg["b"], "seed_A": seed_A, "seed_P": seed_P}
    from rmdq_kem import kem_keygen, kem_encaps, kem_decaps
    _, sk = kem_keygen(p, seed_A, seed_P, seed_S)
    assert sk["s"] == kg["s"]  # deterministic: same seeds -> same key (t=0)
    m = bytes(range(32))
    K, ct, _ = kem_encaps(pk, p, m32=m)
    K2, ok = kem_decaps(sk, ct, p)
    assert ok and K == K2
    ct_bad = {"u": [list(x) for x in ct["u"]], "v": list(ct["v"])}
    ct_bad["v"][0] = (ct_bad["v"][0] + 1) % p.q
    K_bad, ok_bad = kem_decaps(sk, ct_bad, p)
    assert not ok_bad
    kat = {
        "n": p.n, "q": p.q, "k": p.k, "eta": p.eta, "w": p.w, "eta_e": p.eta_e,
        "seed_A_hex": seed_A.hex(),
        "pk_hash_hex": sk["pk_hash"].hex(), "sigma_hex": sk["sigma"].hex(),
        "m_hex": m.hex(), "K_hex": K.hex(), "K_reject_hex": K_bad.hex(),
        "A_flat": [c for row in pk["A"] for poly in row for c in poly],
        "b_flat": flatten(pk["b"]),
        "s_flat": flatten(sk["s"]), "e_flat": flatten(kg["e"]),
        "u_flat": flatten(ct["u"]), "v": ct["v"],
    }
    out = os.path.join(os.path.dirname(__file__), "..", "tests", "kat_kem256.json")
    with open(out, "w") as f:
        json.dump(kat, f)
    print(f"wrote {out} K={K.hex()[:16]}...")

if __name__ == "__main__":
    main()

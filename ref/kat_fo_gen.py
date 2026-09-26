"""FO KAT generator for C cross-check (TOY-16 q=97 for CPA correctness)."""
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from rmdq_toy import Params
from rmdq_kem import kem_keygen, kem_encaps, kem_decaps, _ct_bytes

def main():
    p = Params(n=16, q=97, k=1, eta=1, w=4, eta_e=1, t=2, m=4)
    seed_A, seed_P, seed_S = b"FO-A-00000000000", b"FO-P-00000000000", b"FO-S-00000000000"
    pk, sk = kem_keygen(p, seed_A, seed_P, seed_S)
    K, ct, m = kem_encaps(pk, p, m32=b"\xAB\xCD" + b"\x00" * 30)
    # tampered ct (flip v[0]) -> expected implicit-reject K
    import copy
    ct_bad = {"u": [list(x) for x in ct["u"]], "v": list(ct["v"])}
    ct_bad["v"][0] = (ct_bad["v"][0] + 1) % p.q
    K_bad, ok_bad = kem_decaps(sk, ct_bad, p)
    assert not ok_bad
    kat = {
        "n": p.n, "q": p.q, "k": p.k, "eta": p.eta, "w": p.w, "eta_e": p.eta_e,
        "seed_A_hex": seed_A.hex(), "seed_P_hex": seed_P.hex(), "seed_S_hex": seed_S.hex(),
        "pk_hash_hex": sk["pk_hash"].hex(), "sigma_hex": sk["sigma"].hex(),
        "m_hex": m.hex(), "K_hex": K.hex(),
        "K_reject_hex": K_bad.hex(),
        "b_flat": [c for poly in pk["b"] for c in poly],
        "u_flat": [c for poly in ct["u"] for c in poly],
        "v": ct["v"],
        "s_flat": [c for poly in sk["s"] for c in poly],
    }
    out = os.path.join(os.path.dirname(__file__), "..", "tests", "kat_fo16.json")
    with open(out, "w") as f:
        json.dump(kat, f)
    print(f"wrote {out} K={K.hex()[:16]}... Krej={K_bad.hex()[:16]}...")

if __name__ == "__main__":
    main()

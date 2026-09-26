"""FO CBD KAT generator (toy n=16 q=97): sampling:'cbd' exercises C CBD path."""
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from rmdq_toy import Params, flatten
from rmdq_kem import kem_keygen, kem_encaps, kem_decaps

def main():
    p = Params(n=16, q=97, k=1, eta=1, w=4, eta_e=1, t=2, m=4)
    seed_A, seed_P, seed_S = b"CBD-A-0000000000", b"CBD-P-0000000000", b"CBD-S-0000000000"
    pk, sk = kem_keygen(p, seed_A, seed_P, seed_S, cbd_err=True)
    K, ct, m = kem_encaps(pk, p, m32=b"\xAB\xCD" + b"\x00" * 30, cbd=True)
    K2, ok = kem_decaps(sk, ct, p, cbd=True)
    assert ok and K == K2
    ct_bad = {"u": [list(x) for x in ct["u"]], "v": list(ct["v"])}
    ct_bad["v"][0] = (ct_bad["v"][0] + 1) % p.q
    K_bad, ok_bad = kem_decaps(sk, ct_bad, p, cbd=True)
    assert not ok_bad
    kat = {
        "n": p.n, "q": p.q, "k": p.k, "eta": p.eta, "w": p.w, "eta_e": p.eta_e,
        "sampling": "cbd",
        "seed_A_hex": seed_A.hex(),
        "pk_hash_hex": sk["pk_hash"].hex(), "sigma_hex": sk["sigma"].hex(),
        "m_hex": m.hex(), "K_hex": K.hex(), "K_reject_hex": K_bad.hex(),
        "b_flat": flatten(pk["b"]),
        "u_flat": flatten(ct["u"]), "v": ct["v"],
        "s_flat": flatten(sk["s"]),
    }
    out = os.path.join(os.path.dirname(__file__), "..", "tests", "kat_fo_cbd16.json")
    with open(out, "w") as f:
        json.dump(kat, f)
    print(f"wrote {out}")

if __name__ == "__main__":
    main()

"""Sig v1 KAT generator for C cross-check (TOY-16 q=17)."""
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from rmdq_toy import Params, flatten
from rmdq_sig import sig_keygen
from rmdq_sig_v1 import sig_sign_v1

def flat_eqs(P):
    triples, off, ln = [], [], []
    idx = 0
    for terms in P:
        off.append(idx)
        ln.append(len(terms))
        for c, vi, vj in terms:
            triples.extend([c, vi, vj])
        idx += len(terms)
    return triples, off, ln

def main():
    p = Params(n=16, q=17, k=1, eta=1, w=4, eta_e=1, t=2, m=4)
    pk, sk = sig_keygen(p, b"CSV-A-0000000000", b"CSV-P-0000000000", b"CSV-S-0000000000")
    msg = b"sig v1 KAT msg"
    sig = sig_sign_v1(sk, msg, p)
    triples, off, ln = flat_eqs(pk["P"])
    kat = {
        "n": p.n, "q": p.q, "k": p.k, "t": p.t,
        "seed_A_hex": pk["seed_A"].hex(), "seed_P_hex": pk["seed_P"].hex(),
        "pk_hash_hex": sk["pk_hash"].hex(),
        "msg_hex": msg.hex(), "mu_hex": sig["mu"].hex(),
        "A_flat": [c for row in pk["A"] for col in row for c in col],
        "b_flat": flatten(pk["b"]),
        "P_triples": triples, "P_off": off, "P_len": ln,
        "c_poly": sig["c_poly"], "c_scalar": sig["c_scalar"],
        "z_lat_flat": flatten(sig["z_lat"]), "z_mq_flat": flatten(sig["z_mq"]),
        "h": sig["h"], "w_flat": flatten(sig["w"]), "py": sig["py"],
        "y_flat": flatten(sig["y"]), "gamma": sig["gamma"],
        "attempt": sig["attempt"],
    }
    out = os.path.join(os.path.dirname(__file__), "..", "tests", "kat_sigv1_16.json")
    with open(out, "w") as f:
        json.dump(kat, f)
    print(f"wrote {out}")

if __name__ == "__main__":
    main()

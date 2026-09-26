"""TOY-32 noisy KAT for C full MITM (A,b,P flat + true key for verify)."""
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from rmdq_toy import Params, keygen, flatten

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
    p = Params(n=32, q=97, k=1, eta=1, w=6, eta_e=1, t=3, m=6)
    kg = keygen(p, b"noisy-A-00000000", b"noisy-P-00000000", b"noisy-S-0000000000")
    triples, off, ln = flat_eqs(kg["P"])
    kat = {
        "n": p.n, "q": p.q,
        "A_flat": kg["A"][0][0], "b": kg["b"][0], "s_true": flatten(kg["s"]),
        "P_triples": triples, "P_off": off, "P_len": ln, "t": p.t,
    }
    out = os.path.join(os.path.dirname(__file__), "..", "tests", "kat_toy32_noisy.json")
    with open(out, "w") as f:
        json.dump(kat, f)
    print(f"wrote {out} true_weight={sum(1 for x in kat['s_true'] if x)}")

if __name__ == "__main__":
    main()

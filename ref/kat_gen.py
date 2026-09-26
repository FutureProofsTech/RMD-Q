"""Generate C KAT vectors from Python toy (byte-exact for matrix expansion + CPA)."""
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from rmdq_toy import Params, expand_matrix, keygen, encrypt, flatten

def main():
    p = Params(n=16, q=17, k=1, eta=1, w=4, eta_e=1, t=2, m=4)
    seed_A, seed_P, seed_s, seed_r = b"KAT-A-0000000000", b"KAT-P-0000000000", b"KAT-S-0000000000", b"KAT-R-0000000000"
    kg = keygen(p, seed_A, seed_P, seed_s)
    pk = {"A": kg["A"], "b": kg["b"]}
    m = b"KAT-message-12345678901234567890"[:32].ljust(32, b"\x00")
    ct = encrypt(pk, m, p, seed_r)
    kat = {
        "n": p.n, "q": p.q, "k": p.k,
        "seed_A_hex": seed_A.hex(),
        "A_flat": kg["A"][0][0] if p.k == 1 else [x for row in kg["A"] for col in row for x in col],
        "s_flat": flatten(kg["s"]), "e_flat": flatten(kg["e"]), "b_flat": flatten(kg["b"]),
        "r_flat": flatten(ct["r"]), "u_flat": flatten(ct["u"]), "v": ct["v"],
        "msg_hex": m.hex(),
    }
    out = os.path.join(os.path.dirname(__file__), "..", "tests", "kat_toy16.json")
    with open(out, "w") as f:
        json.dump(kat, f)
    print(f"wrote {out}")

if __name__ == "__main__":
    main()

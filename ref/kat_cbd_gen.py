"""CBD KAT generator: uses canonical rmdq_toy.cbd_poly (single source of truth)."""
import json
import os
import random
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from rmdq_toy import cbd_poly as cbd_py

def main():
    rnd = random.Random(777)
    vecs = []
    for n, eta, q in [(16, 2, 17), (32, 2, 97), (64, 2, 3329)]:
        nbytes = (n * eta * 2 + 7) // 8
        buf = bytes(rnd.randrange(256) for _ in range(nbytes))
        vecs.append({"n": n, "eta": eta, "q": q,
                     "buf_hex": buf.hex(), "poly": cbd_py(buf, n, eta, q)})
    # edge: all-0xFF and all-0x00 (both -> all zeros)
    vecs.append({"n": 4, "eta": 2, "q": 17,
                 "buf_hex": "ffff", "poly": cbd_py(bytes([0xFF, 0xFF]), 4, 2, 17)})
    out = os.path.join(os.path.dirname(__file__), "..", "tests", "kat_cbd.json")
    with open(out, "w") as f:
        json.dump(vecs, f)
    print(f"wrote {out} ({len(vecs)} vectors)")

if __name__ == "__main__":
    main()

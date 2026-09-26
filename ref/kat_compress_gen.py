"""Compress/decompress KAT generator (uses canonical rmdq_toy codec)."""
import json
import os
import random
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from rmdq_toy import compress_poly

def main():
    rnd = random.Random(2026)
    vecs = []
    for d, n, q in [(10, 64, 3329), (5, 64, 3329), (4, 32, 3329), (12, 32, 3329)]:
        poly = [rnd.randrange(q) for _ in range(n)]
        vecs.append({"d": d, "n": n, "q": q, "poly": poly,
                     "comp": compress_poly(poly, d, q)})
    out = os.path.join(os.path.dirname(__file__), "..", "tests", "kat_compress.json")
    with open(out, "w") as f:
        json.dump(vecs, f)
    print(f"wrote {out} ({len(vecs)} vectors)")

if __name__ == "__main__":
    main()

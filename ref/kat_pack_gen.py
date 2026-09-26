"""Pack KAT generator: random coeff vectors at du/dv/logq widths."""
import json
import os
import random
import sys

def pack_py(coeffs, bits):
    acc = accbits = 0
    out = bytearray()
    for c in coeffs:
        acc |= (c & ((1 << bits) - 1)) << accbits
        accbits += bits
        while accbits >= 8:
            out.append(acc & 0xFF)
            acc >>= 8
            accbits -= 8
    if accbits:
        out.append(acc & 0xFF)
    return bytes(out)

def main():
    rnd = random.Random(1234)
    vecs = []
    for bits, n in [(10, 64), (4, 32), (12, 64)]:
        coeffs = [rnd.randrange(1 << bits) for _ in range(n)]
        vecs.append({"bits": bits, "n": n, "coeffs": coeffs, "packed_hex": pack_py(coeffs, bits).hex()})
    out = os.path.join(os.path.dirname(__file__), "..", "tests", "kat_pack.json")
    with open(out, "w") as f:
        json.dump(vecs, f)
    print(f"wrote {out} ({len(vecs)} vectors)")

if __name__ == "__main__":
    main()

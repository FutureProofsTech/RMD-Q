import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ref"))
from rmdq_toy import Params, cbd_poly, sample_cbd_vec, shake128
from rmdq_kem import kem_keygen, kem_encaps, kem_decaps

def test_cbd_matches_legacy_shape():
    # canonical CBD: all-ones buf -> all-zero poly (sums cancel)
    assert cbd_poly(bytes([0xFF] * 8), 16, 2, 97) == [0] * 16
    print("cbd canonical ok")

def test_toy_cbd_fo():
    p = Params(n=16, q=97, k=1, eta=1, w=4, eta_e=1, t=2, m=4)
    pk, sk = kem_keygen(p, b"A" * 16, b"P" * 16, b"S" * 16, cbd_err=True)
    K, ct, m = kem_encaps(pk, p, m32=b"\xAB\xCD" + b"\x00" * 30, cbd=True)
    K2, ok = kem_decaps(sk, ct, p, cbd=True)
    assert ok and K == K2
    ct["v"][0] = (ct["v"][0] + 1) % p.q
    K3, ok3 = kem_decaps(sk, ct, p, cbd=True)
    assert not ok3 and K3 != K
    print("toy CBD FO ok")

def test_kem256_cbd_fo():
    p = Params(n=256, q=3329, k=2, eta=2, w=64, eta_e=2, t=0, m=0)
    pk, sk = kem_keygen(p, b"CBD256-A-0000000", b"CBD256-P-0000000", b"CBD256-S-000000000"[:16])
    m = bytes(range(32))
    K, ct, _ = kem_encaps(pk, p, m32=m, cbd=True)
    K2, ok = kem_decaps(sk, ct, p, cbd=True)
    assert ok and K == K2
    print("kem256 CBD FO ok")

if __name__ == "__main__":
    test_cbd_matches_legacy_shape()
    test_toy_cbd_fo()
    test_kem256_cbd_fo()
    print("ALL CBD TESTS PASSED")

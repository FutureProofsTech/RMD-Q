import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ref"))
from rmdq_toy import Params, keygen, encrypt, decrypt, flatten
from rmdq_ntt import mat_vec_mul_ntt
from rmdq_kem import kem_keygen, kem_encaps, kem_decaps

P256 = Params(n=256, q=3329, k=2, eta=2, w=128, eta_e=2, t=0, m=0)

def test_ntt_path_matches_schoolbook():
    p = P256
    kg = keygen(p, b"NTT-A-0000000000", b"NP", b"NTT-S-0000000000")
    r = mat_vec_mul_ntt(kg["A"], kg["s"], p.q, p.n, p.k)
    from rmdq_toy import mat_vec_mul
    assert r == mat_vec_mul(kg["A"], kg["s"], p.q), "NTT mat-vec must match schoolbook at n=256"
    print("ntt path matches schoolbook (k=2 n=256)")

def test_kem256_roundtrip():
    p = P256
    pk, sk = kem_keygen(p, b"K256-A-00000000", b"K256-P-00000000", b"K256-S-00000000")
    m = bytes(range(32))
    K, ct, mout = kem_encaps(pk, p, m32=m)
    assert mout == m
    K2, ok = kem_decaps(sk, ct, p)
    assert ok and K == K2, "FO roundtrip n=256"
    ct["v"][0] = (ct["v"][0] + 1) % p.q
    K3, ok3 = kem_decaps(sk, ct, p)
    assert not ok3 and K3 != K, "tamper must reject"
    print("kem256 FO ok (encaps/decaps/reject, full 32B msg)")

if __name__ == "__main__":
    test_ntt_path_matches_schoolbook()
    test_kem256_roundtrip()
    print("ALL KEM256 TESTS PASSED")

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ref"))
from rmdq_toy import Params
from rmdq_kem import kem_keygen, kem_encaps, kem_decaps
from rmdq_sig import sig_keygen, sig_sign, sig_verify

def test_kem_roundtrip_toy32():
    # q=97 for CPA correctness (q=17 failure rate documented in attack catalog)
    p = Params(n=16, q=97, k=1, eta=1, w=4, eta_e=1, t=2, m=4)
    pk, sk = kem_keygen(p, b"KEM-A-test-00000", b"KEM-P-test-00000", b"KEM-S-test-00000")
    K, ct, m = kem_encaps(pk, p, m32=b"\xab" * 32)
    K2, ok = kem_decaps(sk, ct, p)
    assert ok and K == K2, "FO roundtrip must pass"
    # tamper
    ct["v"][0] = (ct["v"][0] + 1) % p.q
    K3, ok3 = kem_decaps(sk, ct, p)
    assert not ok3 and K3 != K, "tamper must trigger implicit rejection"
    print("kem fo ok (encaps/decaps/reject)")

def test_sig_roundtrip():
    p = Params(n=16, q=17, k=1, eta=1, w=4, eta_e=1, t=2, m=4)
    pk, sk = sig_keygen(p, b"SIG-A-test-00000", b"SIG-P-test-00000", b"SIG-S-test-00000")
    sig = sig_sign(sk, b"hello rmdq toy", p)
    ok, reason = sig_verify(pk, b"hello rmdq toy", sig, p)
    assert ok, f"verify must pass: {reason}"
    ok2, _ = sig_verify(pk, b"tampered", sig, p)
    assert not ok2, "tampered msg must reject"
    print(f"sig ok (c={sig['c']} attempt={sig['attempt']})")

def test_kat_determinism():
    p = Params(n=16, q=97, k=1, eta=1, w=4, eta_e=1, t=2, m=4)
    pk1, sk1 = kem_keygen(p, b"A" * 16, b"P" * 16, b"S" * 16)
    K1, ct1, _ = kem_encaps(pk1, p, m32=b"\x42" * 32)
    pk2, sk2 = kem_keygen(p, b"A" * 16, b"P" * 16, b"S" * 16)
    K2, ct2, _ = kem_encaps(pk2, p, m32=b"\x42" * 32)
    assert K1 == K2 and str(ct1) == str(ct2), "deterministic coins must give same KAT"
    print("kat determinism ok")

if __name__ == "__main__":
    test_kem_roundtrip_toy32()
    test_sig_roundtrip()
    test_kat_determinism()
    print("ALL KEM+SIG TESTS PASSED")

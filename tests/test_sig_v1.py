import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ref"))
from rmdq_toy import Params
from rmdq_sig import sig_keygen
from rmdq_sig_v1 import sig_sign_v1, sig_verify_v1

def test_sig_v1():
    p = Params(n=16, q=17, k=1, eta=1, w=4, eta_e=1, t=2, m=4)
    pk, sk = sig_keygen(p, b"V1-A-test-00000", b"V1-P-test-00000", b"V1-S-test-00000")
    sig = sig_sign_v1(sk, b"v1 hello", p)
    assert sum(1 for x in sig["c_poly"] if x) == 2, "tau=2"
    ok, r = sig_verify_v1(pk, b"v1 hello", sig, p)
    assert ok, f"v1 verify: {r}"
    ok2, _ = sig_verify_v1(pk, b"tamper", sig, p)
    assert not ok2
    print(f"sig v1 ok (c_scalar={sig['c_scalar']} attempt={sig['attempt']})")

if __name__ == "__main__":
    test_sig_v1()
    print("SIG V1 PASSED")

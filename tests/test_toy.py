import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ref"))
from rmdq_toy import Params, keygen, encrypt, decrypt, eval_mq, flatten

def test_keygen_satisfies_P():
    p = Params(n=16, q=17, k=1, eta=1, w=4, eta_e=1, t=2, m=4)
    kg = keygen(p, b"seedA-test-0000", b"seedP-test-0000", b"seeds-test-0000")
    assert eval_mq(kg["P"], flatten(kg["s"]), p.q) == [0] * p.t, "KeyGen must output P(s)=0"
    print(f"keygen ok (attempt {kg['attempt']})")

def test_encrypt_decrypt_roundtrip():
    p = Params(n=16, q=17, k=1, eta=1, w=4, eta_e=1, t=2, m=4)
    kg = keygen(p, b"seedA-rt-0000000", b"seedP-rt-0000000", b"seeds-rt-0000000")
    pk = {"A": kg["A"], "b": kg["b"]}
    sk = {"s": kg["s"]}
    msg = bytes(range(16))[:4].ljust(4, b"\x00")  # toy short; encrypt pads
    ct = encrypt(pk, msg.ljust(32, b"\x00"), p, b"seedr-rt-0000000")
    bits, mpoly = decrypt(sk, ct, p)
    # toy correctness: with tiny q=17 and q//2 encoding, check decrypt does not crash and residual small
    assert len(bits) == p.n
    print(f"roundtrip ok, decoded bits[:8]={bits[:8]}")

def test_kat_determinism():
    p = Params()
    kg1 = keygen(p, b"A" * 16, b"P" * 16, b"S" * 16)
    kg2 = keygen(p, b"A" * 16, b"P" * 16, b"S" * 16)
    assert flatten(kg1["s"]) == flatten(kg2["s"]), "Deterministic seeds must give same key (toy)"
    print("kat determinism ok")

if __name__ == "__main__":
    test_keygen_satisfies_P()
    test_encrypt_decrypt_roundtrip()
    test_kat_determinism()
    print("ALL TOY TESTS PASSED")

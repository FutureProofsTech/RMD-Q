import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ref"))
from rmdq_toy import Params, flatten, eval_mq, shake256
from rmdq_planted import keygen_planted
import rmdq_kem as K

P256J = Params(n=256, q=3329, k=2, eta=2, w=64, eta_e=2, t=8, m=12)

def test_planted_joint_256():
    p = P256J
    kg = keygen_planted(p, b"PJ-A-0000000000", b"PJ-P-0000000000", b"PJ-S-0000000000")
    assert all(v == 0 for v in eval_mq(kg["P"], flatten(kg["s"]), p.q))
    assert all(len(e) == p.m for e in kg["P"]), "constant term count"
    pk = {"A": kg["A"], "P": kg["P"], "b": kg["b"],
          "seed_A": b"PJ-A-0000000000", "seed_P": b"PJ-P-0000000000"}
    pk_hash = shake256(K._pk_bytes(pk, p) + pk["seed_A"] + pk["seed_P"], 32)
    sk = {"s": kg["s"], "pk": pk, "pk_hash": pk_hash,
          "sigma": shake256(b"implicit-reject" + b"PJ-S-0000000000", 32)}
    m = bytes(range(32))
    KK, ct, _ = K.kem_encaps(pk, p, m32=m)
    K2, ok = K.kem_decaps(sk, ct, p)
    assert ok and KK == K2
    print(f"planted joint n=256/t=8 ok (pure-random {sum(kg['meta']['pure_random'])}/{len(kg['P'])})")

if __name__ == "__main__":
    test_planted_joint_256()
    print("PLANTED JOINT PASSED")

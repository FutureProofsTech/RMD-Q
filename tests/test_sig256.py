import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ref"))
from rmdq_toy import Params, flatten, eval_mq, shake256
from rmdq_planted import keygen_planted
from rmdq_sig import _pk_hash, sig_sign, sig_verify

P256S = Params(n=256, q=3329, k=2, eta=2, w=64, eta_e=2, t=8, m=12)

def test_sig256_planted_v0():
    p = P256S
    kg = keygen_planted(p, b"PS-A-0000000000", b"PS-P-0000000000", b"PS-S-0000000000")
    assert all(v == 0 for v in eval_mq(kg["P"], flatten(kg["s"]), p.q))
    pk = {"A": kg["A"], "P": kg["P"], "b": kg["b"],
          "seed_A": b"PS-A-0000000000", "seed_P": b"PS-P-0000000000"}
    sk = {"s": kg["s"], "pk": pk, "pk_hash": _pk_hash(pk, p)}
    # gamma=2^15 toy-at-scale: shift c*s (<=4) negligible vs width (hiding ok);
    # mod-q norm checks are vacuous at this width (recorded z_bound, see docs).
    # What this KAT proves: challenge/w'/MQ machinery + tamper rejection.
    sig = sig_sign(sk, b"sig256 hello", p, gamma=1 << 15)
    ok, reason = sig_verify(pk, b"sig256 hello", sig, p)
    assert ok, f"verify: {reason}"
    ok2, _ = sig_verify(pk, b"tampered", sig, p)
    assert not ok2
    print(f"sig256 planted v0 ok (attempt {sig['attempt']})")

if __name__ == "__main__":
    test_sig256_planted_v0()
    print("SIG256 PASSED")

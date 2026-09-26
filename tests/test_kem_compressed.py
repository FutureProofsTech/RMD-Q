import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ref"))
from rmdq_toy import Params, compress_poly, decompress_poly
from rmdq_kem import kem_keygen, kem_encaps, kem_decaps

P256 = Params(n=256, q=3329, k=2, eta=2, w=128, eta_e=2, t=0, m=0)
DU, DV = 10, 5


def compress_ct(ct, du=DU, dv=DV, q=3329):
    return ([compress_poly(p, du, q) for p in ct["u"]],
            compress_poly(ct["v"], dv, q))


def decompress_ct(cu, cv, du=DU, dv=DV, q=3329):
    return ({"u": [decompress_poly(p, du, q) for p in cu],
             "v": decompress_poly(cv, dv, q)})


def test_compress_codec():
    import random
    rnd = random.Random(11)
    for d in (4, 5, 10, 12):
        poly = [rnd.randrange(3329) for _ in range(64)]
        rt = decompress_poly(compress_poly(poly, d, 3329), d, 3329)
        err = max(abs((a - b) % 3329 if (a - b) % 3329 <= 1664 else (a - b) % 3329 - 3329)
                  for a, b in zip(poly, rt))
        assert err <= 3329 // (2 ** (d + 1)) + 1, (d, err)
    print("compress codec bounds ok")


def test_compressed_roundtrip():
    for cbd in (False, True):
        p = P256
        pk, sk = kem_keygen(p, b"CC-A-0000000000", b"CC-P-0000000000", b"CC-S-0000000000",
                            cbd_err=cbd)
        m = bytes(range(32))
        K, ct, _ = kem_encaps(pk, p, m32=m, cbd=cbd, du=DU, dv=DV)
        nbits = sum(len(x) for x in ct["u"]) * DU + len(ct["v"]) * DV
        assert nbits == (2 * 256 * DU + 256 * DV), nbits
        K2, ok = kem_decaps(sk, ct, p, cbd=cbd, du=DU, dv=DV)
        assert ok and K2 == K, f"compressed FO roundtrip cbd={cbd}"
        # tamper compressed ct -> implicit reject
        bad = {"u": [list(x) for x in ct["u"]], "v": list(ct["v"])}
        bad["v"][0] = (bad["v"][0] + 1) % (1 << DV)
        K3, ok3 = kem_decaps(sk, bad, p, cbd=cbd, du=DU, dv=DV)
        assert not ok3 and K3 != K
        print(f"compressed ({DU},{DV}) FO ok cbd={cbd} ({nbits // 8}B ct)")


if __name__ == "__main__":
    test_compress_codec()
    test_compressed_roundtrip()
    print("ALL COMPRESSED TESTS PASSED")

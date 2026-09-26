"""Diagnostics for planted-MQ distribution (toy scale, fast)."""
import sys
sys.path.insert(0, "ref")
from rmdq_toy import Params, flatten, eval_mq
from rmdq_planted import plant_mq, keygen_planted
from collections import Counter


def test_always_satisfied():
    for n, q, k, t, m in [(16, 17, 1, 2, 4), (32, 97, 1, 3, 6), (64, 3329, 2, 4, 8)]:
        N = n * k
        import random
        rnd = random.Random(0)
        s = [rnd.choice([0, 1, q - 1]) if rnd.random() < 0.3 else 0 for _ in range(N)]
        P, meta = plant_mq(f"seed-{n}".encode(), s, t, m, q)
        assert all(v == 0 for v in eval_mq(P, s, q)), (n, q)
        assert all(len(e) == m for e in P)
    print("planting always satisfied + shape ok")


def test_keygen_planted_toy():
    p = Params(n=16, q=17, k=1, eta=1, w=4, eta_e=1, t=2, m=4)
    for i in range(5):
        kg = keygen_planted(p, f"A{i}".encode().ljust(16, b"0")[:16],
                            f"P{i}".encode().ljust(16, b"0")[:16],
                            f"S{i}".encode().ljust(16, b"0")[:16])
        assert all(v == 0 for v in eval_mq(kg["P"], flatten(kg["s"]), p.q))
    print("planted keygen toy ok (5/5 first-try)")


def test_fix_position_spread():
    # fix positions should spread over support(s), not collapse to one coord
    p = Params(n=32, q=97, k=1, eta=1, w=8, eta_e=1, t=6, m=6)
    kg = keygen_planted(p, b"A" * 16, b"P" * 16, b"S" * 16)
    pos = []
    for fp in kg["meta"]["fix_pos"]:
        pos.extend(fp if isinstance(fp, tuple) else [fp])
    supp = {i for i, x in enumerate(flatten(kg["s"])) if x}
    assert set(pos) <= supp, "fix positions must lie on support(s)"
    print(f"fix spread: {len(set(pos))} distinct coords over support size {len(supp)}; "
          f"shapes={Counter(kg['meta']['fix_shape'])}")


def test_coeff_chisquare():
    # TRUE fix coefficients (tracked slots), non-pure-random eqs only.
    # H0: uniform over Z_q^* (nonzero enforced by resampling) -> df=15.
    import random
    from rmdq_planted import plant_mq
    q, N, m, t = 17, 32, 6, 400
    rnd = random.Random(3)
    s = [rnd.choice([0, 1, q - 1]) if rnd.random() < 0.4 else 0 for _ in range(N)]
    if not any(s):
        s[0] = 1
    P, meta = plant_mq(b"chi-seed-0000000", s, t, m, q)
    fixc = [P[e][meta["fix_slot"][e]][0] for e in range(t)
            if not meta["pure_random"][e]]
    obs = Counter(fixc)
    n = len(fixc)
    print(f"nonzero-fix eqs: {n}/{t} (rest pure-random)")
    if n > 2 * (q - 1):
        chi = sum((obs.get(v, 0) - n / (q - 1)) ** 2 / (n / (q - 1))
                  for v in range(1, q))
        print(f"fix-coeff chi2={chi:.1f} (n={n}, H0 mean=15, 3-sigma bar~31)")


if __name__ == "__main__":
    test_always_satisfied()
    test_keygen_planted_toy()
    test_fix_position_spread()
    test_coeff_chisquare()
    print("PLANTED DIAGNOSTICS DONE")

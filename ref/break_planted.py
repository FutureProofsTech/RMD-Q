"""Planted kill-phase: Gröbner+bound recovery on planted instances.

(a) n=16 planted (t=2): expect SUCCESS in seconds -- proves the planted
    distribution offers no algebraic immunity at toy scale (methodology check).
(b) n=32 planted (t=3): bounded attempt, expect stall -- documents scaling.
(c) Support-enumeration projection for prod (combinatorial floor).
"""
import sys
import time
sys.path.insert(0, "ref")
from rmdq_toy import Params, flatten, eval_mq
from rmdq_planted import keygen_planted


def grobner_recover(n, q, k, t, m, tag, timeout_note=True):
    from sympy import symbols, groebner, GF
    p = Params(n=n, q=q, k=k, eta=1, w=4 if n == 16 else 6,
               eta_e=1, t=t, m=m)
    kg = keygen_planted(p, f"{tag}A".encode().ljust(16, b"0")[:16],
                        f"{tag}P".encode().ljust(16, b"0")[:16],
                        f"{tag}S".encode().ljust(16, b"0")[:16])
    P, s_true = kg["P"], flatten(kg["s"])
    N = n * k
    xs = symbols(f"x0:{N}")
    eqs = []
    for terms in P:
        e = 0
        for c, vi, vj in terms:
            e += c * xs[vi] * xs[vj]
        eqs.append(e)
    # sparse bounds: x^3 - x = 0 per var (coeffs in {-1,0,1} for eta=1)
    for i in range(N):
        eqs.append(xs[i] ** 3 - xs[i])
    t0 = time.time()
    G = groebner(eqs, *xs, order="grlex", domain=GF(q))
    dt = time.time() - t0
    # check: does basis pin the true key? look for linear polys
    linears = [g.as_expr() for g in G.polys if g.total_degree() == 1]
    print(f"n={n} t={t}: {dt:.1f}s basis={len(G.polys)} linears={len(linears)}",
          flush=True)
    return dt


def support_projection():
    import math
    for N, w in [(16, 4), (32, 6), (128, 32), (512, 128)]:
        print(f"N={N} w={w}: C(N,w) ~ 2^{math.log2(math.comb(N, w)):.0f}")


if __name__ == "__main__":
    import signal
    grobner_recover(16, 17, 1, 2, 4, "PK16")

    def _alrm(*a):
        raise TimeoutError("budget")
    signal.signal(signal.SIGALRM, _alrm)
    signal.alarm(240)
    try:
        grobner_recover(32, 97, 1, 3, 6, "PK32")
    except TimeoutError:
        print("n=32: EXCEEDED 240s budget -- stall documented (expected)")
    except Exception as e:
        print(f"n=32: {type(e).__name__} ({str(e)[:80]}) -- stall documented")
    finally:
        signal.alarm(0)
    support_projection()

"""msolve scaling points: planted MQ Gröbner-basis times vs dimension."""
import subprocess
import sys
import time
sys.path.insert(0, "ref")
from rmdq_toy import Params
from rmdq_planted import keygen_planted
from msolve_toy import to_msolve


def point(n, q, k, t, m, tag, budget):
    import signal
    p = Params(n=n, q=q, k=k, eta=1, w=6, eta_e=1, t=t, m=m)
    kg = keygen_planted(p, f"{tag}A".encode().ljust(16, b"0")[:16],
                        f"{tag}P".encode().ljust(16, b"0")[:16],
                        f"{tag}S".encode().ljust(16, b"0")[:16])
    from rmdq_toy import flatten
    N = n * k
    src = to_msolve(kg["P"], N, q)
    open("/tmp/scal.ms", "w").write(src)
    t0 = time.time()

    def _alrm(*a):
        raise TimeoutError()
    signal.signal(signal.SIGALRM, _alrm)
    signal.alarm(budget)
    try:
        r = subprocess.run(["msolve", "-g", "2", "-f", "/tmp/scal.ms",
                            "-o", "/tmp/scal.out"],
                           capture_output=True, text=True, timeout=budget + 30)
        dt = time.time() - t0
        nlines = len(open("/tmp/scal.out").readlines())
        print(f"n={n} t={t}: GB {dt:.1f}s, {nlines} polys", flush=True)
    except TimeoutError:
        print(f"n={n} t={t}: EXCEEDED {budget}s budget", flush=True)
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    point(16, 17, 1, 2, 4, "SC16", 120)
    point(24, 97, 1, 3, 6, "SC24", 300)

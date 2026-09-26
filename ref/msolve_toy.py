"""msolve cross-check on planted toy MQ (vs sympy timing)."""
import subprocess
import sys
sys.path.insert(0, "ref")
from rmdq_toy import Params
from rmdq_planted import keygen_planted
from rmdq_toy import flatten


def to_msolve(P, N, q, bounds=True):
    # msolve input format: vars line, characteristic line, polys (one per
    # line, comma-separated/trailing comma tolerated per --help).
    lines = [",".join(f"x{i}" for i in range(N)), str(q)]
    polys = []
    for terms in P:
        parts = []
        for c, vi, vj in terms:
            if vj == -1:
                parts.append(f"{c}*x{vi}")
            else:
                parts.append(f"{c}*x{vi}*x{vj}")
        polys.append(" + ".join(parts) if parts else "0")
    if bounds:
        for i in range(N):
            polys.append(f"x{i}^3 - x{i}")
    lines.extend(p + "," for p in polys)
    return "\n".join(lines) + "\n"


def main():
    import time
    p = Params(n=16, q=17, k=1, eta=1, w=4, eta_e=1, t=2, m=4)
    kg = keygen_planted(p, b"MS-A-0000000000", b"MS-P-0000000000", b"MS-S-0000000000")
    src = to_msolve(kg["P"], 16, 17)
    open("/tmp/planted16.ms", "w").write(src)
    t0 = time.time()
    r = subprocess.run(["msolve", "-g", "2", "-f", "/tmp/planted16.ms",
                        "-o", "/tmp/planted16.out"],
                       capture_output=True, text=True, timeout=300)
    dt = time.time() - t0
    print(f"msolve -g2 planted n=16: {dt:.1f}s rc={r.returncode}")
    nlines = len(open("/tmp/planted16.out").readlines())
    print(f"GB lines: {nlines}")
    print("(sympy reference: 2.1s basis-53 on same shape; full msolve solve"
          " without -g exceeds 300s on this box -- solving >> basis)")


if __name__ == "__main__":
    main()

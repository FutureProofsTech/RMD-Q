"""Degree-of-regularity study: planted vs random MQ (msolve -v2 signals).

For each instance: max F4 round degree, max matrix dimensions, wall time.
Compares planted-RMD-Q systems against uniform-random MQ of identical shape
(same n/t/m/sparsity, no planted solution) to detect non-genericity: if
planted instances solve at systematically lower degree, the planting shapes
the algebraic structure (attacker-favorable finding, must be reported).
Also compares against the Bardet semi-regular prediction for random systems.
"""
import re
import subprocess
import sys
import time
sys.path.insert(0, "ref")
from rmdq_toy import Params, expand_mq, flatten
from rmdq_planted import keygen_planted


def to_msolve(P, N, q, bounds=True, eta=1):
    lines = [",".join(f"x{i}" for i in range(N)), str(q)]
    for terms in P:
        parts = []
        for c, vi, vj in terms:
            parts.append(f"{c}*x{vi}" if vj == -1 else f"{c}*x{vi}*x{vj}")
        lines.append((" + ".join(parts) if parts else "0") + ",")
    if bounds:
        # sparse value bounds: x(x-1)...(x-eta)(x+1)...(x+eta) = 0
        for i in range(N):
            fac = [f"x{i}"]
            for v in range(1, eta + 1):
                fac.append(f"(x{i} - {v})")
                fac.append(f"(x{i} + {v})")
            lines.append(("*".join(fac)) + ",")
    return "\n".join(lines) + "\n"


def run_msolve(src, budget):
    open("/tmp/dreg.ms", "w").write(src)
    t0 = time.time()
    try:
        r = subprocess.run(["msolve", "-g", "2", "-v", "2", "-f", "/tmp/dreg.ms",
                            "-o", "/tmp/dreg.out"],
                           capture_output=True, text=True, timeout=budget)
        dt = time.time() - t0
    except subprocess.TimeoutExpired:
        return {"timeout": True}
    degs, mats = [2], [(0, 0)]  # default: input degree, nothing learned
    for line in (r.stdout + r.stderr).splitlines():
        m = re.match(r"\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*x\s*(\d+)", line)
        if m:
            degs.append(int(m.group(1)))
            mats.append((int(m.group(4)), int(m.group(5))))
    return {"timeout": False, "time": dt, "rc": r.returncode,
            "maxdeg": max(degs), "maxmat": max(a * b for a, b in mats)}


def bardet_dreg(n, degs):
    """First d with nonpositive coeff of prod_i (1-z^{d_i})^{m_i} / (1-z)^n.
    degs = list of (degree, count), e.g. [(2,t),(3,N)] for MQ + cubics."""
    from math import comb

    def coeff_of(num, d):
        # num = list of (deg, cnt): expand product of (1-z^deg)^cnt to degree d
        from functools import reduce
        poly = [1] + [0] * d
        for deg, cnt in num:
            # multiply by (1 - z^deg)^cnt truncated
            from math import comb as C
            factor = [0] * (d + 1)
            k = 0
            while k * deg <= d and k <= cnt:
                factor[k * deg] = ((-1) ** k) * C(cnt, k)
                k += 1
            new = [0] * (d + 1)
            for i in range(d + 1):
                for j in range(d + 1 - i):
                    new[i + j] += poly[i] * factor[j]
            poly = new
        return poly[d]

    for d in range(2, 80):
        s = sum(coeff_of(degs, d - j) * comb(n + j - 1, j)
                if d - j >= 0 else 0 for j in range(d + 1))
        if s <= 0:
            return d
    return None


def point(n, q, k, t, m, tag, budget, planted, bounds):
    p = Params(n=n, q=q, k=k, eta=1, w=6, eta_e=1, t=t, m=m)
    if planted:
        kg = keygen_planted(p, f"{tag}A".encode().ljust(16, b"0")[:16],
                            f"{tag}P".encode().ljust(16, b"0")[:16],
                            f"{tag}S".encode().ljust(16, b"0")[:16])
        P = kg["P"]
    else:
        P = expand_mq(f"{tag}R".encode(), t, n * k, m, q)
    # NOTE: no field equations here (pure MQ comparison; bounds studied sep.)
    r = run_msolve(to_msolve(P, n * k, q, bounds=bounds), budget)
    kind = "planted" if planted else "random "
    if r.get("timeout"):
        print(f"{kind} n={n} t={t}: TIMEOUT {budget}s", flush=True)
    else:
        print(f"{kind} n={n} t={t}: {r['time']:.1f}s maxdeg={r['maxdeg']} "
              f"maxmat={r['maxmat']}", flush=True)
    return r


if __name__ == "__main__":
    print("Bardet d_reg (MQ + cubic bounds, semi-regular model):")
    for n, t in [(16, 2), (32, 3), (512, 8)]:
        print(f"  n={n} t={t}: d_reg={bardet_dreg(n, [(2, t), (3, n)])}")
    print("msolve GB runs (homogeneous-quad + cubic bounds):", flush=True)
    for bounds in (False, True):
        print(f"--- bounds={bounds} ---", flush=True)
        point(16, 17, 1, 2, 4, "DG16", 120, True, bounds)
        point(16, 17, 1, 2, 4, "DG16", 120, False, bounds)

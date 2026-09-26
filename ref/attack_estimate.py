"""Attack cost sketches for RMD-Q (toy calibration, NOT a real estimator)."""
import math

def log2_space(N, w, eta):
    if w > N:
        return float("inf")
    c = math.comb(N, w)
    return math.log2(c) + w * math.log2(2 * eta + 1)

def report(name, n, q, k, eta, w_per_poly, t):
    N = n * k
    w_tot = w_per_poly * k
    s = log2_space(N, w_tot, eta)
    print(f"{name}: N={N} w_tot={w_tot} eta={eta} t={t} q={q}")
    print(f"  brute log2(S) ~ {s:.1f} bits, Grover ~ {s/2:.1f} bits")
    print(f"  lattice dim ~ {2*N} (MLWE embed), MQ filter 2^-{t*math.log2(q):.1f} per random candidate")
    print()

if __name__ == "__main__":
    report("TOY-16", 16, 17, 1, 1, 4, 2)
    report("TOY-32", 32, 97, 1, 1, 6, 3)
    report("MID-64", 64, 3329, 2, 2, 16, 4)
    report("PROD-SKETCH-256", 256, 3329, 2, 2, 64, 8)
    print("Kill criteria: TOY-16/32 must be <40 bits (breakable). Prod must be >260 bits conjectured.")

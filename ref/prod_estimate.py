"""PROD-256 size + cost sketch (conjectured, not claimed)."""
import math

def log2_space(N, w, eta):
    return math.log2(math.comb(N, w)) + w * math.log2(2 * eta + 1)

def report(n=256, q=3329, k=2, eta=2, w=64, t=8, m=12, du=10, dv=4):
    N = n * k
    wt = w * k
    s = log2_space(N, wt, eta)
    logq = math.log2(q)
    pk = (k * n * logq) / 8 + 64  # b + seeds
    ct = (k * n * du + n * dv) / 8
    # sig v1 dual opening: z_lat + z_mq (k polys each, gamma-sized ~ log) + c + h + w hint (unoptimized)
    sig = (2 * k * n * logq) / 8 + 512
    print(f"PROD n={n} q={q} k={k} eta={eta} w={w}/poly t={t}")
    print(f"  N={N} wt={wt} brute log2={s:.0f} Grover={s/2:.0f} (need >256/128 for Cat1-ish sketch)")
    print(f"  lattice dim~{2*N}, MQ filter 2^-{t*logq:.0f} per random lattice candidate")
    print(f"  sizes (unpacked toy-style): pk~{pk/1024:.1f}KB ct~{ct/1024:.1f}KB sig~{sig/1024:.1f}KB")
    print(f"  NOTE: q=17 slack vacuous in toy; prod q=3329 slack meaningful. Sig 2x openings unoptimized.")

if __name__ == "__main__":
    report()
    report(k=3, w=80, t=10)

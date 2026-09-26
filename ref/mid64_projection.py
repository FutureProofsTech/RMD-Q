"""MID-64 MITM cost projection from measured TOY-32 rate."""
import math
import sys
sys.path.insert(0, "ref")
from rmdq_toy import Params

def log2_space(N, w, eta):
    return math.log2(math.comb(N, w)) + w * math.log2(2 * eta + 1)

def main():
    # Measured: TOY-32 full MITM 23.35M pair-checks broke wt=3 key (space was smaller than max).
    # Calibrate: Python pair-check ~ 25M / T_python. C did 23.35M in <500s => >46k pairs/s.
    # Use C rate 50k pairs/s as conservative floor for projection.
    rate = 50000
    for name, N, w, eta in [("TOY-16", 16, 4, 1), ("TOY-32", 32, 6, 1),
                            ("MID-64", 128, 32, 2), ("PROD-256 k=2", 512, 128, 2)]:
        s = log2_space(N, w, eta)
        # MITM square-root shape: ~2^(s/2) table + probes (ignores noise/MQ overhead)
        years = 2 ** (s / 2) / rate / 3600 / 24 / 365
        print(f"{name}: N={N} wt={w} log2(S)={s:.0f} MITM-shape ~2^{s/2:.0f} ops ~ {years:.1e} years @ {rate}/s")
    print("note: noise residual + MQ filter add overhead beyond pure MITM shape; lattice-BKZ hybrid differs.")

if __name__ == "__main__":
    main()

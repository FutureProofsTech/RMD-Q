"""Packed sizes + C stack measurement (gcc -fstack-usage)."""
import math
import os
import subprocess

def packed_bits(n, q, k, du=10, dv=4, eta=2, w=None, t=8):
    logq = math.log2(q)
    # pk: b (k polys, logq bits/coeff, could compress to du) + 64B seeds
    pk_full = k * n * logq / 8 + 64
    pk_c = k * n * du / 8 + 64
    ct = (k * n * du + n * dv) / 8
    # sk: s sparse: positions (log2(N) bits) + signs/values; dense fallback k*n*3 bits (eta=2 -> 3 bits)
    N = k * n
    wt = (w or 64) * k
    sk_sparse = wt * (math.log2(N) + 3) / 8 + 64
    # sig v1 dual: z_lat+z_mq; each coeff ~logq unpacked, ~ (logq-2) packed with gamma bound; rough
    sig = (2 * k * n * logq) / 8 + 256
    return pk_full, pk_c, ct, sk_sparse, sig

def stack_usage():
    cdir = os.path.join(os.path.dirname(__file__), "..", "c")
    r = subprocess.run(["gcc", "-std=c90", "-O2", "-fstack-usage", "-c", "rmdq.c", "-o", "/tmp/rmdq.o"],
                       cwd=cdir, capture_output=True, text=True)
    out = {}
    try:
        with open("/tmp/rmdq.su") as f:
            for line in f:
                out[line.split()[0]] = line.strip()
    except OSError:
        pass
    # also kem_fo / sig_v1 frames
    subprocess.run(["gcc", "-std=c90", "-O2", "-fstack-usage", "-c", "kem_fo.c", "-o", "/tmp/kem_fo.o"],
                   cwd=cdir, capture_output=True, text=True)
    subprocess.run(["gcc", "-std=c90", "-O2", "-fstack-usage", "-c", "sig_v1.c", "-o", "/tmp/sig_v1.o"],
                   cwd=cdir, capture_output=True, text=True)
    frames = {}
    for obj in ["/tmp/kem_fo.su", "/tmp/sig_v1.su", "/tmp/rmdq.su"]:
        try:
            with open(obj) as f:
                for line in f:
                    parts = line.strip().split("\t")
                    # file:line:col:func \t bytes \t qual
                    frames[parts[0]] = parts[1] + "B " + parts[2]
        except OSError:
            pass
    return out, frames

if __name__ == "__main__":
    for k, w, t in [(2, 64, 8), (3, 80, 10), (4, 96, 12)]:
        pf, pc, ct, sk, sg = packed_bits(256, 3329, k, w=w, t=t)
        print(f"k={k}: pk_full~{pf/1024:.2f}KB pk_comp~{pc/1024:.2f}KB ct~{ct/1024:.2f}KB sk_sparse~{sk/1024:.2f}KB sig~{sg/1024:.2f}KB")
    _, frames = stack_usage()
    print("C stack frames (static, bytes):")
    for k in sorted(frames):
        print(f"  {k}: {frames[k]}")

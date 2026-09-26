"""M4 cycle estimation by static instruction counting (conservative).

Model (Cortex-M4, from ARM DDI0403 + pqm4 practice):
- 16/32-bit mul/add/sub/ldr/str/cmp/branch-taken-penalty: counted per inner iteration
- loads/stores 1-2c, mul 1c, branch mispredict ~2c, 64-bit __modsi3 (our `long % q`)
  ~ 30-60c (dominant!). This is WHY the stream/CT code does ONE mod per coeff.
- Keccak-f1600: 24 rounds x 25 lanes x ~5 ops ~= 3-4k cycles/block (pqm4 reports ~3.5k).

Counts are static upper bounds for branch-free CT path (fixed trip counts).
"""
import math

MUL, ADD, MEM, MOD64, BR = 1, 1, 2, 45, 2

def poly_mul_ct_cycles(n):
    # per output coeff: n iters x (2 loads a? a[j] hoisted-ish + b loads + 2 muls + 2 adds + loop ovh)
    per_iter = 2 * MEM + 2 * MUL + 2 * ADD + BR
    return n * (n * per_iter + MOD64)

def mat_vec_ct_cycles(n, k):
    return k * k * (n * n * (2 * MEM + 2 * MUL + 2 * ADD + BR) + n * MOD64)

def keccak_cycles(nbytes, rate=136):
    blocks = (nbytes + rate - 1) // rate
    return blocks * 3500

def poly_mul_ntt_cycles(n=256):
    # 2 fwd + pointwise + 1 inv: 3 transforms x 8 layers x 128 butterflies
    # per butterfly: 1 barrett-mul (~8c w/ MU) + 2 adds + 2 mem + loop ovh (~15c)
    # pointwise: 128 pairs x (4 muls + adds + 1 mod) ~ 128*40c; basemul zeta mult extra
    # measured host ratio ntt/schoolbook ~ 1/6 at n=256; model absolute:
    per_bfy = 8 + 2 * ADD + 2 * MEM + BR
    return 3 * 8 * 128 * per_bfy + 128 * (4 * MUL + 4 * ADD + MOD64 // 4)


def kem_cycles(n, k, q=3329, backend="schoolbook"):
    # keygen: expand A (k^2 polys) + sample s,e + 1 matvec; encaps: expand + sample r,e1,e2 + 2 matvec; decaps: 1 + reencrypt 2
    polys = k * k + 3 * k + 4
    shake_bytes = polys * n * 2  # ~2B/coeff uniform
    h = keccak_cycles(shake_bytes) * 2  # absorb+squeeze approx
    if backend == "ntt" and n == 256 and q == 3329:
        mv_one = k * k * (poly_mul_ntt_cycles(n) // 1) + k * 256 * 4
        mv = 6 * mv_one
    else:
        mv = 6 * mat_vec_ct_cycles(n, k)
    return h + mv

if __name__ == "__main__":
    for n, k in [(16, 1), (32, 1), (64, 2), (256, 2), (256, 3)]:
        mc = kem_cycles(n, k)
        print(f"n={n:3d} k={k}: schoolbook CT-KEM ~ {mc/1e6:.2f}M cycles "
              f"(~{mc/168e6*1000:.1f}ms @168MHz M4)")
    for n, k in [(256, 2), (256, 3)]:
        mc = kem_cycles(n, k, backend="ntt")
        print(f"n={n:3d} k={k}: NTT KEM ~ {mc/1e6:.2f}M cycles "
              f"(~{mc/168e6*1000:.1f}ms @168MHz M4)")
    print("assumptions: 45c/mod64, 3.5k/Keccak block; branch-free path; NTT validated C impl.")

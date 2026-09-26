/* NTT for (q=3329, n=256). See ntt.h. Tables generated, schedule verified
 * against CRT reduction + schoolbook in ref/ntt_gen.py. C90. */
#include "ntt.h"
#include "rmdq.h"
#include "ntt_tables.h"

#define Q 3329
/* Shared NTT scratch workspace (single-threaded ONLY): all entry points
 * reuse it sequentially; never hold pointers across calls. Max single use:
 * mat-vec Ahat(4096)+shat(1024)+ohat(1024) = 6144 ints. This replaces
 * ~60KB of per-function statics with 24KB shared (see m4-check). */
static int ntt_ws[16 * 256 + 4 * 256 + 4 * 256];
#define WS_AHAT (ntt_ws)
#define WS_SHAT (ntt_ws + 16 * 256)
#define WS_OHAT (ntt_ws + 16 * 256 + 4 * 256)
#define WS_FA (ntt_ws)
#define WS_FB (ntt_ws + 256)
/* Barrett q=3329, SHIFT=26, MU=20158: valid for x in [0,(Q-1)^2]; 1 correction max
 * (exhaustively verified in selftest). */
#define NTT_MU 20158
static int barrett_u32(unsigned long x) {
    unsigned long t = (x * NTT_MU) >> 26;
    unsigned long r = x - t * Q;
    if (r >= Q) r -= Q;
    if (r >= Q) r -= Q; /* safety; verified max 1 needed */
    return (int)r;
}

void rmdq_ntt_fwd(int *a) {
    int len, start, j, k = 1;
    for (len = 128; len >= 2; len >>= 1) {
        for (start = 0; start < 256; start += 2 * len) {
            int zeta = RMDQ_FWT[k++];
            for (j = start; j < start + len; j++) {
                int t = barrett_u32((unsigned long)zeta * (unsigned long)a[j + len]);
                int x = a[j] - t;
                int y = a[j] + t - Q;
                /* branch-free reduce to [0,Q): x may be [-Q+1,Q-1] */
                if (x < 0) x += Q;
                if (y < 0) y += Q;
                if (y >= Q) y -= Q;
                a[j + len] = x;
                a[j] = y;
            }
        }
    }
}

void rmdq_ntt_inv(int *a) {
    /* mirror layers len=2..128; twiddle index map rebuilt identically, reversed */
    int lens[7], starts[7], li = 0;
    int len, L = 128;
    int k = 1;
    while (L >= 2) { lens[li] = L; starts[li] = k; k += 128 / L; L >>= 1; li++; }
    /* lens[] = {128,64,...,2}, starts[] = k-offset per layer */
    for (li = 6; li >= 0; li--) {
        int B, bb, j;
        len = lens[li];
        B = 128 / len;
        for (bb = 0; bb < B; bb++) {
            int zi = RMDQ_ZINVW[starts[li] + bb];
            int jj;
            for (jj = 0; jj < len; jj++) {
                j = bb * 2 * len + jj;
                {
                    int u = a[j], v = a[j + len];
                    int s = u + v;
                    int d = u - v;
                    if (s >= Q) s -= Q;
                    if (d < 0) d += Q;
                    a[j] = s;
                    a[j + len] = barrett_u32((unsigned long)d * (unsigned long)zi);
                }
            }
        }
    }
    for (k = 0; k < 256; k++)
        a[k] = barrett_u32((unsigned long)a[k] * (unsigned long)RMDQ_NINV128);
}

void rmdq_poly_mul_ntt(const int *a, const int *b, int *out, int n, int q) {
    if (n != 256 || q != Q) {
        /* fallback: schoolbook stream (toy params) */
        int k, j;
        for (k = 0; k < n; k++) {
            long sum = 0;
            for (j = 0; j < n; j++) {
                int b1 = k - j;
                if (b1 >= 0) sum += (long)a[j] * b[b1];
                else sum -= (long)a[j] * b[b1 + n];
            }
            {
                long v = sum % q;
                if (v < 0) v += q;
                out[k] = (int)v;
            }
        }
        return;
    }
    {
        int *fa = WS_FA, *fb = WS_FB;
        int i;
        for (i = 0; i < 256; i++) { fa[i] = a[i]; fb[i] = b[i]; }
        rmdq_ntt_fwd(fa);
        rmdq_ntt_fwd(fb);
        for (i = 0; i < 128; i++) {
            int a0 = fa[2*i], a1 = fa[2*i+1];
            int b0 = fb[2*i], b1 = fb[2*i+1];
            int z = RMDQ_ZP[i];
            long c0 = (long)a0*b0 + (long)a1*b1*z;
            long c1 = (long)a0*b1 + (long)a1*b0;
            fa[2*i] = (int)(c0 % Q < 0 ? c0 % Q + Q : c0 % Q);
            fa[2*i+1] = (int)(c1 % Q < 0 ? c1 % Q + Q : c1 % Q);
        }
        rmdq_ntt_inv(fa);
        for (i = 0; i < 256; i++) out[i] = fa[i];
    }
}

/* ---- constant-time shape twins (masked arithmetic, no data branches) ----
 * Reductions assume inputs already in [0,Q) (NTT domain invariant) except
 * where noted. Arithmetic >>31 on negatives is implementation-defined but
 * universal on gcc/x86_64+ARM; equivalence vs branching twins is proven in
 * selftest on LCG vectors, plus objdump smoke check (see docs/05). */

static int sub_q_masked(int x) {
    /* x in [0,2Q) -> [0,Q) */
    x -= Q;
    x += Q & (x >> 31);
    return x;
}

static int add_q_masked(int x) {
    /* x in (-Q,Q) -> [0,Q) */
    x += Q & (x >> 31);
    return x;
}

void rmdq_ntt_fwd_ct(int *a) {
    int len, start, j, k = 1;
    for (len = 128; len >= 2; len >>= 1) {
        for (start = 0; start < 256; start += 2 * len) {
            int zeta = RMDQ_FWT[k++];
            for (j = start; j < start + len; j++) {
                int t = barrett_u32((unsigned long)zeta * (unsigned long)a[j + len]);
                a[j + len] = add_q_masked(a[j] - t);
                a[j] = sub_q_masked(a[j] + t);
            }
        }
    }
}

void rmdq_ntt_inv_ct(int *a) {
    int lens[7], starts[7], li = 0;
    int len, L = 128;
    int k = 1;
    while (L >= 2) { lens[li] = L; starts[li] = k; k += 128 / L; L >>= 1; li++; }
    for (li = 6; li >= 0; li--) {
        int B, bb, j;
        len = lens[li];
        B = 128 / len;
        for (bb = 0; bb < B; bb++) {
            int zi = RMDQ_ZINVW[starts[li] + bb];
            for (j = bb * 2 * len; j < bb * 2 * len + len; j++) {
                int u = a[j], v = a[j + len];
                int s = u + v;
                int d = u - v;
                s = sub_q_masked(s);
                d = add_q_masked(d);
                a[j] = s;
                a[j + len] = barrett_u32((unsigned long)d * (unsigned long)zi);
            }
        }
    }
    for (k = 0; k < 256; k++)
        a[k] = barrett_u32((unsigned long)a[k] * (unsigned long)RMDQ_NINV128);
}

void rmdq_poly_mul_ntt_ct(const int *a, const int *b, int *out, int n, int q) {
    if (n != 256 || q != Q) {
        rmdq_poly_mul_ct(a, b, out, n, q);
        return;
    }
    {
        int *fa = WS_FA, *fb = WS_FB;
        int i;
        for (i = 0; i < 256; i++) { fa[i] = a[i]; fb[i] = b[i]; }
        rmdq_ntt_fwd_ct(fa);
        rmdq_ntt_fwd_ct(fb);
        for (i = 0; i < 128; i++) {
            int p1 = barrett_u32((unsigned long)fa[2*i] * (unsigned long)fb[2*i]);
            int p2 = barrett_u32((unsigned long)fa[2*i+1] * (unsigned long)fb[2*i+1]);
            int p3 = barrett_u32((unsigned long)p2 * (unsigned long)RMDQ_ZP[i]);
            int p4 = barrett_u32((unsigned long)fa[2*i] * (unsigned long)fb[2*i+1]);
            int p5 = barrett_u32((unsigned long)fa[2*i+1] * (unsigned long)fb[2*i]);
            int c0 = p1 + p3;
            int c1 = p4 + p5;
            fa[2*i] = sub_q_masked(c0);
            fa[2*i+1] = sub_q_masked(c1);
        }
        rmdq_ntt_inv_ct(fa);
        for (i = 0; i < 256; i++) out[i] = fa[i];
    }
}

/* Mat-vec via NTT, constant-time shape: CT transforms, Barrett basemul,
 * masked accumulation (acc invariant [0,Q)). Falls back to schoolbook CT. */
void rmdq_mat_vec_mul_ntt_ct(const int *A, const int *s, int *out, const rmdq_params *p) {
    if (p->n != 256 || p->q != Q || p->k > RMDQ_MAXK) {
        int i, j, t;
        /* schoolbook CT fallback (duplicated small to avoid dispatch churn) */
        for (i = 0; i < p->k; i++)
            for (t = 0; t < p->n; t++) {
                long sum = 0;
                for (j = 0; j < p->k; j++) {
                    const int *aij = A + (i * p->k + j) * p->n;
                    const int *sj = s + j * p->n;
                    int u;
                    for (u = 0; u < p->n; u++) {
                        int v = t - u;
                        int sv = (v >= 0) ? sj[v] : sj[v + p->n];
                        int sgn = (v >= 0) ? 1 : -1;
                        sum += (long)sgn * aij[u] * sv;
                    }
                }
                {
                    /* branch-free reduce (toy fallback; % itself remains an
                     * instruction-level timing caveat, documented in docs/05).
                     * Comparison compiles to setcc (no jump); avoids width
                     * assumptions of arithmetic-shift masks. */
                    long v = sum % p->q;
                    v += (long)p->q & -(v < 0);
                    out[i * p->n + t] = (int)v;
                }
            }
        return;
    }
    {
        int *Ahat = WS_AHAT, *shat = WS_SHAT, *ohat = WS_OHAT;
        int i, j, t;
        for (i = 0; i < p->k; i++)
            for (j = 0; j < p->k; j++) {
                int tmp[256];
                for (t = 0; t < 256; t++) tmp[t] = A[(i * p->k + j) * 256 + t];
                rmdq_ntt_fwd_ct(tmp);
                for (t = 0; t < 256; t++) Ahat[(i * p->k + j) * 256 + t] = tmp[t];
            }
        for (j = 0; j < p->k; j++) {
            int tmp[256];
            for (t = 0; t < 256; t++) tmp[t] = s[j * 256 + t];
            rmdq_ntt_fwd_ct(tmp);
            for (t = 0; t < 256; t++) shat[j * 256 + t] = tmp[t];
        }
        for (i = 0; i < p->k; i++) {
            int acc[256];
            for (t = 0; t < 256; t++) acc[t] = 0;
            for (j = 0; j < p->k; j++) {
                int k2;
                for (k2 = 0; k2 < 128; k2++) {
                    int a0 = Ahat[(i * p->k + j) * 256 + 2 * k2];
                    int a1 = Ahat[(i * p->k + j) * 256 + 2 * k2 + 1];
                    int b0 = shat[j * 256 + 2 * k2];
                    int b1 = shat[j * 256 + 2 * k2 + 1];
                    int p1 = barrett_u32((unsigned long)a0 * (unsigned long)b0);
                    int p2 = barrett_u32((unsigned long)a1 * (unsigned long)b1);
                    int p3 = barrett_u32((unsigned long)p2 * (unsigned long)RMDQ_ZP[k2]);
                    int p4 = barrett_u32((unsigned long)a0 * (unsigned long)b1);
                    int p5 = barrett_u32((unsigned long)a1 * (unsigned long)b0);
                    int c0 = sub_q_masked(p1 + p3);
                    int c1 = sub_q_masked(p4 + p5);
                    acc[2 * k2] = sub_q_masked(acc[2 * k2] + c0);
                    acc[2 * k2 + 1] = sub_q_masked(acc[2 * k2 + 1] + c1);
                }
            }
            for (t = 0; t < 256; t++) ohat[i * 256 + t] = acc[t];
            rmdq_ntt_inv_ct(ohat + i * 256);
            for (t = 0; t < 256; t++) out[i * 256 + t] = ohat[i * 256 + t];
        }
    }
}

/* Mat-vec via NTT: transform each A entry and s entry once, pointwise * accumulate in NTT domain, single inverse per output row. Falls back to
 * streaming schoolbook unless q==3329 && n==256. */
void rmdq_mat_vec_mul_ntt(const int *A, const int *s, int *out, const rmdq_params *p) {
    if (p->n != 256 || p->q != Q || p->k > RMDQ_MAXK) {
        rmdq_mat_vec_mul_stream(A, s, out, p);
        return;
    }
    {
        int *Ahat = WS_AHAT, *shat = WS_SHAT, *ohat = WS_OHAT;
        int i, j, t;
        for (i = 0; i < p->k; i++)
            for (j = 0; j < p->k; j++) {
                int tmp[256];
                for (t = 0; t < 256; t++) tmp[t] = A[(i * p->k + j) * 256 + t];
                rmdq_ntt_fwd(tmp);
                for (t = 0; t < 256; t++) Ahat[(i * p->k + j) * 256 + t] = tmp[t];
            }
        for (j = 0; j < p->k; j++) {
            int tmp[256];
            for (t = 0; t < 256; t++) tmp[t] = s[j * 256 + t];
            rmdq_ntt_fwd(tmp);
            for (t = 0; t < 256; t++) shat[j * 256 + t] = tmp[t];
        }
        for (i = 0; i < p->k; i++) {
            int acc[256];
            for (t = 0; t < 256; t++) acc[t] = 0;
            for (j = 0; j < p->k; j++) {
                int k2;
                /* pointwise accumulation must respect pair structure:
                 * accumulate full 256-vec pointwise then basemul-style fold?
                 * Correct approach: accumulate per-pair linear combinations
                 * in the CRT domain: out_hat[pair] = sum_j Ahat*MUL shat
                 * where MUL is basemul mod (X^2-Z). */
                for (k2 = 0; k2 < 128; k2++) {
                    int a0 = Ahat[(i * p->k + j) * 256 + 2 * k2];
                    int a1 = Ahat[(i * p->k + j) * 256 + 2 * k2 + 1];
                    int b0 = shat[j * 256 + 2 * k2];
                    int b1 = shat[j * 256 + 2 * k2 + 1];
                    int z = RMDQ_ZP[k2];
                    long c0 = (long)a0 * b0 + (long)a1 * b1 * z;
                    long c1 = (long)a0 * b1 + (long)a1 * b0;
                    long e0 = acc[2 * k2] + c0;
                    long e1 = acc[2 * k2 + 1] + c1;
                    acc[2 * k2] = (int)(e0 % Q);
                    acc[2 * k2 + 1] = (int)(e1 % Q);
                }
            }
            /* normalize acc to [0,Q) then inverse */
            for (t = 0; t < 256; t++) { acc[t] %= Q; if (acc[t] < 0) acc[t] += Q; }
            for (t = 0; t < 256; t++) ohat[i * 256 + t] = acc[t];
            rmdq_ntt_inv(ohat + i * 256);
            for (t = 0; t < 256; t++) out[i * 256 + t] = ohat[i * 256 + t];
        }
    }
}

void rmdq_ntt_batch_fwd(int *a, int count) {
    int c;
    for (c = 0; c < count; c++)
        rmdq_ntt_fwd(a + c * 256);
}

/* Ahat-precomputed mat-vec: caller transforms A once (batch_fwd over k*k
 * polys) and reuses across ops (multi-encaps sessions, re-encrypt checks). */
void rmdq_mat_vec_mul_ahat(const int *Ahat, const int *s, int *out, const rmdq_params *p) {
    if (p->n != 256 || p->q != Q || p->k > RMDQ_MAXK) {
        rmdq_mat_vec_mul_stream(Ahat, s, out, p);
        return;
    }
    {
        int *shat = WS_SHAT, *ohat = WS_OHAT;
        int i, j, t;
        for (j = 0; j < p->k; j++) {
            int tmp[256];
            for (t = 0; t < 256; t++) tmp[t] = s[j * 256 + t];
            rmdq_ntt_fwd(tmp);
            for (t = 0; t < 256; t++) shat[j * 256 + t] = tmp[t];
        }
        for (i = 0; i < p->k; i++) {
            int acc[256];
            for (t = 0; t < 256; t++) acc[t] = 0;
            for (j = 0; j < p->k; j++) {
                int k2;
                for (k2 = 0; k2 < 128; k2++) {
                    int a0 = Ahat[(i * p->k + j) * 256 + 2 * k2];
                    int a1 = Ahat[(i * p->k + j) * 256 + 2 * k2 + 1];
                    int b0 = shat[j * 256 + 2 * k2];
                    int b1 = shat[j * 256 + 2 * k2 + 1];
                    int z = RMDQ_ZP[k2];
                    long c0 = (long)a0 * b0 + (long)a1 * b1 * z;
                    long c1 = (long)a0 * b1 + (long)a1 * b0;
                    long e0 = acc[2 * k2] + c0;
                    long e1 = acc[2 * k2 + 1] + c1;
                    acc[2 * k2] = (int)(e0 % Q);
                    acc[2 * k2 + 1] = (int)(e1 % Q);
                }
            }
            for (t = 0; t < 256; t++) { acc[t] %= Q; if (acc[t] < 0) acc[t] += Q; }
            for (t = 0; t < 256; t++) ohat[i * 256 + t] = acc[t];
            rmdq_ntt_inv(ohat + i * 256);
            for (t = 0; t < 256; t++) out[i * 256 + t] = ohat[i * 256 + t];
        }
    }
}

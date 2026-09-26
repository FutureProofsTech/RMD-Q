/* Portable C90 implementation. No malloc, no float. */
#include "rmdq.h"

void rmdq_mat_vec_mul_stream(const int *A, const int *s, int *out, const rmdq_params *p);

void rmdq_poly_add(const int *a, const int *b, int *out, int n, int q) {
    int i;
    for (i = 0; i < n; i++) {
        int v = a[i] + b[i];
        v %= q;
        if (v < 0) v += q;
        out[i] = v;
    }
}

void rmdq_poly_sub(const int *a, const int *b, int *out, int n, int q) {
    int i;
    for (i = 0; i < n; i++) {
        int v = a[i] - b[i];
        v %= q;
        if (v < 0) v += q;
        out[i] = v;
    }
}

void rmdq_poly_mul(const int *a, const int *b, int *out, int n, int q) {
    int tmp[512]; /* 2*256 max */
    int i, j;
    for (i = 0; i < 2 * n; i++) tmp[i] = 0;
    for (i = 0; i < n; i++) {
        if (a[i] == 0) continue;
        for (j = 0; j < n; j++) {
            if (b[j] == 0) continue;
            tmp[i + j] = (tmp[i + j] + a[i] * b[j]) % q;
        }
    }
    for (i = 0; i < n; i++) out[i] = tmp[i];
    for (i = n; i < 2 * n; i++) {
        out[i - n] -= tmp[i];
        out[i - n] %= q;
        if (out[i - n] < 0) out[i - n] += q;
    }
}

/* Streaming: per-output-coeff accumulation, O(1) stack besides output.
 * For out[k]: sum over j of a[j]*b[k-j] (j<=k) minus sum over j of a[j]*b[k-j+n]
 * (wrap with negacyclic sign). Single mod per coeff. Output identical. */
void rmdq_poly_mul_stream(const int *a, const int *b, int *out, int n, int q) {
    int k, j;
    for (k = 0; k < n; k++) {
        long sum = 0;
        for (j = 0; j < n; j++) {
            if (a[j] == 0) continue;
            {
                int bj1 = k - j;
                if (bj1 >= 0 && b[bj1]) sum += (long)a[j] * b[bj1];
            }
            {
                int bj2 = k - j + n;
                if (bj2 >= 0 && bj2 < n && b[bj2]) sum -= (long)a[j] * b[bj2];
            }
        }
        {
            long v = sum % q;
            if (v < 0) v += q;
            out[k] = (int)v;
        }
    }
}

int rmdq_norm_inf(const int *a, int n, int q) {
    int m = 0, i;
    for (i = 0; i < n; i++) {
        int c = a[i] % q;
        if (c < 0) c += q;
        if (c > q / 2) c = c - q;
        if (c < 0) c = -c;
        if (c > m) m = c;
    }
    return m;
}

int rmdq_weight(const int *a, int n) {
    int w = 0, i;
    for (i = 0; i < n; i++) if (a[i] != 0) w++;
    return w;
}

void rmdq_mat_vec_mul(const int *A, const int *s, int *out, const rmdq_params *p) {
    /* Legacy buffered variant kept for compat; forwards to streaming core
     * so all callers get O(1) stack even if not yet switched. */
    rmdq_mat_vec_mul_stream(A, s, out, p);
}

/* out[i][t] = sum_j sum_u A[i][j][u] * s[j][(t-u) mod n, negacyclic].
 * Sparse-skipping (fast) variant; see _ct for branch-free. */
void rmdq_mat_vec_mul_stream(const int *A, const int *s, int *out, const rmdq_params *p) {
    int i, j, t, u;
    for (i = 0; i < p->k; i++) {
        for (t = 0; t < p->n; t++) {
            long sum = 0;
            for (j = 0; j < p->k; j++) {
                const int *aij = A + (i * p->k + j) * p->n;
                const int *sj = s + j * p->n;
                for (u = 0; u < p->n; u++) {
                    int a = aij[u];
                    if (!a) continue;
                    {
                        int v = t - u;
                        if (v >= 0) {
                            if (sj[v]) sum += (long)a * sj[v];
                        } else {
                            v += p->n;
                            if (sj[v]) sum -= (long)a * sj[v];
                        }
                    }
                }
            }
            {
                long v = sum % p->q;
                if (v < 0) v += p->q;
                out[i * p->n + t] = (int)v;
            }
        }
    }
}

/* Branch-free mat-vec: same math, no zero-skips. Fixed trip counts. */
void rmdq_mat_vec_mul_ct(const int *A, const int *s, int *out, const rmdq_params *p) {
    int i, j, t, u;
    for (i = 0; i < p->k; i++) {
        for (t = 0; t < p->n; t++) {
            long sum = 0;
            for (j = 0; j < p->k; j++) {
                const int *aij = A + (i * p->k + j) * p->n;
                const int *sj = s + j * p->n;
                for (u = 0; u < p->n; u++) {
                    int v = t - u;
                    int sv = (v >= 0) ? sj[v] : sj[v + p->n];
                    int sgn = (v >= 0) ? 1 : -1;
                    sum += (long)sgn * aij[u] * sv;
                }
            }
            {
                long v = sum % p->q;
                if (v < 0) v += p->q;
                out[i * p->n + t] = (int)v;
            }
        }
    }
}

/* Branch-free shape: identical arithmetic, no `if (x==0) continue`, no early
 * exits. Inner loop always executes n iterations with masked add via multiply
 * by (a[i]!=0)&(b[j]!=0) expressed branchlessly. Note: `?:` compiles to cmov
 * at O2 on x86_64/ARM; verify disassembly for prod. Accumulates in long. */
void rmdq_poly_mul_ct(const int *a, const int *b, int *out, int n, int q) {
    int k, j;
    for (k = 0; k < n; k++) {
        long sum = 0;
        for (j = 0; j < n; j++) {
            int aj = a[j];
            int b1 = k - j;
            int v1 = (b1 >= 0) ? b[b1] : 0;
            int b2 = k - j + n;
            int v2 = (b2 >= 0 && b2 < n) ? b[b2] : 0;
            /* branchless: mask selects, arithmetic always runs */
            sum += (long)aj * v1;
            sum -= (long)aj * v2;
        }
        {
            long v = sum % q;
            if (v < 0) v += q;
            out[k] = (int)v;
        }
    }
}

void rmdq_mq_eval(const int *triples, const int *eq_off, const int *eq_len,
                  int t, const int *s_flat, int N, int q, int *out) {
    int e, j;
    (void)N;
    for (e = 0; e < t; e++) {
        long acc = 0;
        for (j = 0; j < eq_len[e]; j++) {
            int c = triples[(eq_off[e] + j) * 3];
            int vi = triples[(eq_off[e] + j) * 3 + 1];
            int vj = triples[(eq_off[e] + j) * 3 + 2];
            if (vj == -1) acc += (long)c * s_flat[vi];
            else acc += (long)c * s_flat[vi] * s_flat[vj];
        }
        out[e] = (int)(acc % q);
    }
}

void rmdq_poly_scalar_mul(const int *a, int c, int *out, int n, int q) {
    int i;
    for (i = 0; i < n; i++) out[i] = (int)(((long)a[i] * c) % q);
}

void rmdq_cbd(const unsigned char *buf, int n, int eta, int q, int *out) {    /* Kyber-style CBD_eta: d = sum_{j<eta} bit(2*i*eta+j) - bit((2*i+1)*eta+j).
     * Branch-free: fixed loops, bit ops only. buf layout: consecutive bits. */
    int i, j;
    for (i = 0; i < n; i++) {
        int d = 0;
        for (j = 0; j < eta; j++) {
            int bitpos0 = (2 * i * eta + j);
            int bitpos1 = ((2 * i + 1) * eta + j);
            int b0 = (buf[bitpos0 >> 3] >> (bitpos0 & 7)) & 1;
            int b1 = (buf[bitpos1 >> 3] >> (bitpos1 & 7)) & 1;
            d += b0 - b1;
        }
        d %= q;
        if (d < 0) d += q;
        out[i] = d;
    }
}

int rmdq_pack(const int *coeffs, int n, int bits, unsigned char *out) {
    long acc = 0;
    int accbits = 0, oi = 0, i;
    for (i = 0; i < n; i++) {
        acc |= (long)(coeffs[i] & ((1 << bits) - 1)) << accbits;
        accbits += bits;
        while (accbits >= 8) {
            out[oi++] = (unsigned char)(acc & 0xFF);
            acc >>= 8;
            accbits -= 8;
        }
    }
    if (accbits) out[oi++] = (unsigned char)(acc & 0xFF);
    return oi;
}

int rmdq_unpack(const unsigned char *in, int n, int bits, int *coeffs) {    long acc = 0;
    int accbits = 0, ii = 0, i;
    int mask = (1 << bits) - 1;
    for (i = 0; i < n; i++) {
        while (accbits < bits) {
            acc |= (long)in[ii++] << accbits;
            accbits += 8;
        }
        coeffs[i] = (int)(acc & mask);
        acc >>= bits;
        accbits -= bits;
    }
    return ii;
}

void rmdq_sample_sparse_rb(const unsigned char *rb, int rblen,
                           int n, int q, int eta, int w, int *out) {
    /* Mirrors Python sample_sparse_poly exactly, including STABLE insertion
     * sort (matches sorted() semantics on ties). TEST-ONLY (variable-time).
     * Compiled out under RMDQ_NO_LEGACY (retired distribution). */
#ifndef RMDQ_NO_LEGACY
    /* Mirrors Python sample_sparse_poly exactly, including STABLE insertion
     * sort (matches sorted() semantics on ties). TEST-ONLY (variable-time). */
    int order[256], keep[256], cnt = 0;
    int i, j;
    for (i = 0; i < n; i++) {
        int b = rb[i] % (2 * eta + 1);
        int v = b - eta;
        out[i] = v;
        if (v != 0) cnt++;
        order[i] = i;
    }
    if (cnt > w) {
        for (i = 1; i < n; i++) {
            int oi = order[i], ki = rb[(n + oi) % rblen];
            j = i - 1;
            while (j >= 0 && rb[(n + order[j]) % rblen] > ki) {
                order[j + 1] = order[j];
                j--;
            }
            order[j + 1] = oi;
        }
        for (i = 0; i < n; i++) keep[i] = 0;
        for (i = 0; i < w; i++) keep[order[i]] = 1;
        for (i = 0; i < n; i++) if (!keep[i]) out[i] = 0;
    }
    for (i = 0; i < n; i++) {
        out[i] %= q;
        if (out[i] < 0) out[i] += q;
    }
#else
    (void)rb; (void)rblen; (void)n; (void)q; (void)eta; (void)w; (void)out;
#endif
}

/* Kyber-style compression, exact integer arithmetic (round-half-up via
 * +q//2 / +2^{d-1}); bit-identical to Python compress/decompress_poly. */
void rmdq_compress(const int *poly, int n, int d, int q, int *out) {
    int i;
    for (i = 0; i < n; i++) {
        int x = poly[i] % q;
        long c;
        if (x < 0) x += q;
        c = ((long)x << d) + q / 2;
        c /= q;
        out[i] = (int)(c % (1L << d));
    }
}

void rmdq_decompress(const int *comp, int n, int d, int q, int *out) {
    int i;
    for (i = 0; i < n; i++) {
        long y = ((long)comp[i] * q + (1L << (d - 1))) / (1L << d);
        out[i] = (int)(y % q);
    }
}

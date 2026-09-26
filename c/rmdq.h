/* UQ-New RMD-Q portable C skeleton (C90, no float, no dynamic alloc).
 * Ring arithmetic + sparse + MQ eval only. SHAKE plug-in point documented.
 * NOT audited. Self-test via `make test`.
 */
#ifndef RMDQ_H
#define RMDQ_H

#define RMDQ_MAXN 256
#define RMDQ_MAXK 4

typedef struct {
    int n;
    int q;
    int k;
    int eta;
    int w;
    int eta_e;
    int t;
} rmdq_params;

/* out = (a+b) mod q, len n */
void rmdq_poly_add(const int *a, const int *b, int *out, int n, int q);
/* out = (a-b) mod q */
void rmdq_poly_sub(const int *a, const int *b, int *out, int n, int q);
/* out = a*b in Z_q[X]/(X^n+1), naive O(n^2), skips zeros */
void rmdq_poly_mul(const int *a, const int *b, int *out, int n, int q);
/* streaming variant: O(n) stack (long acc, no tmp[2n]); byte-identical output */
void rmdq_poly_mul_stream(const int *a, const int *b, int *out, int n, int q);
/* centered norm: max |c| with c in [-(q-1)/2,(q-1)/2] */
int rmdq_norm_inf(const int *a, int n, int q);
/* hamming weight */
int rmdq_weight(const int *a, int n);
/* out = A*s, A is k*k*n ints row-major, s is k*n, out k*n */
void rmdq_mat_vec_mul(const int *A, const int *s, int *out, const rmdq_params *p);
/* streaming variant: O(1) extra stack, identical output; uses stream mul accumulation */
void rmdq_mat_vec_mul_stream(const int *A, const int *s, int *out, const rmdq_params *p);
/* constant-time shape: no zero-skips, fixed loop trip counts, no data branches.
 * Output identical. Slower on sparse inputs by design. */
void rmdq_poly_mul_ct(const int *a, const int *b, int *out, int n, int q);
/* MQ eval: eqs flat as (coeff,vi,vj) triples, vj=-1 => linear term coeff*x_vi.
 * eq_off[e] = start index into triples for equation e, eq_len[e] = #terms.
 * s_flat len N=k*n. out[t] mod q. */
void rmdq_mq_eval(const int *triples, const int *eq_off, const int *eq_len,
                  int t, const int *s_flat, int N, int q, int *out);
/* out = (c_scalar * a) mod q */
void rmdq_poly_scalar_mul(const int *a, int c, int *out, int n, int q);
/* bit packing: coeffs in [0,2^bits), little-endian bit stream.
 * pack: out needs ceil(n*bits/8) bytes. unpack: inverse. Returns bytes used. */
int rmdq_pack(const int *coeffs, int n, int bits, unsigned char *out);
int rmdq_unpack(const unsigned char *in, int n, int bits, int *coeffs);
/* Kyber-style lossy compression (exact integer arithmetic, matches Python
 * compress_poly/decompress_poly bit-for-bit). */
void rmdq_compress(const int *poly, int n, int d, int q, int *out);
void rmdq_decompress(const int *comp, int n, int d, int q, int *out);
/* CBD sampler, constant-time shape: eta=2 -> coeffs in [-2,2] from 4*eta bits
 * per coeff (Kyber-style: sum(eta bits) - sum(eta bits)). Fixed loops, no
 * data branches on secrets. buf needs n*eta*2/8 bytes. Output 0..q-1. */
void rmdq_cbd(const unsigned char *buf, int n, int eta, int q, int *out);
/* Legacy sparse sampler (test-only, variable-time): coeffs in [-eta,eta] then
 * sparsify to weight w via STABLE insertion sort on rb keys (matches Python
 * sorted() semantics exactly). rb needs rblen bytes; keys use rb[(n+i)%rblen].
 * Use rblen=64 for n<=32 legacy KATs, 2*n beyond (mirrors Python _rb_len). */
void rmdq_sample_sparse_rb(const unsigned char *rb, int rblen,
                           int n, int q, int eta, int w, int *out);
/* Mul dispatch: default streaming (fast, sparse-skipping); override with
 * -DRMDQ_MUL=rmdq_poly_mul_ct for hardened branch-free builds. */
#ifndef RMDQ_MUL
#define RMDQ_MUL rmdq_poly_mul_stream
#endif
#ifndef RMDQ_MATVEC
#define RMDQ_MATVEC rmdq_mat_vec_mul_stream
#endif
void rmdq_mat_vec_mul_ct(const int *A, const int *s, int *out, const rmdq_params *p);

#endif

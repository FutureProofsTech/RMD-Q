/* Benchmark: sparse-skipping stream vs branch-free CT mul at n=16/64/256.
 * Also mat_vec_stream timing for MID-64/PROD-256 projection.
 * Build: gcc -O2 -o bench bench.c rmdq.c && ./bench
 */
#include <stdio.h>
#include <time.h>
#include "rmdq.h"
#include "ntt.h"

static void fill(int *p, int n, int q, int sparse, unsigned seed) {
    int i;
    unsigned s = seed;
    for (i = 0; i < n; i++) {
        s = s * 1103515245u + 12345u;
        if (sparse && (s % 4)) p[i] = 0;
        else p[i] = (int)((s >> 8) % (unsigned)q);
    }
}

static double bench_mul(void (*f)(const int*,const int*,int*,int,int),
                         int *a, int *b, int *o, int n, int q, int reps) {
    int r;
    clock_t t = clock();
    for (r = 0; r < reps; r++) f(a, b, o, n, q);
    return (double)(clock() - t) / CLOCKS_PER_SEC / reps * 1e6;
}

int main(void) {
    static int a[256], b[256], o[256];
    static int A[4*256], s[4*256], out[4*256];
    int n, reps;
    int ns[] = {16, 64, 256};
    int i;
    printf("poly mul us/op (sparse inputs, w~25%%):\n");
    for (i = 0; i < 3; i++) {
        double t1, t2;
        n = ns[i];
        reps = (n <= 16) ? 20000 : (n <= 64 ? 2000 : 200);
        fill(a, n, 3329, 1, 11);
        fill(b, n, 3329, 1, 22);
        t1 = bench_mul(rmdq_poly_mul_stream, a, b, o, n, 3329, reps);
        t2 = bench_mul(rmdq_poly_mul_ct, a, b, o, n, 3329, reps);
        printf("  n=%3d stream=%8.2f ct=%8.2f ratio=%.2f\n", n, t1, t2, t2 / t1);
    }
    printf("mat_vec_stream us/op (k=2..4, n=64/256, dense):\n");    {
        rmdq_params p;
        double t;
        int k, reps2 = 200, r;
        clock_t tt;
        for (k = 2; k <= 4; k += 2) {
            p.n = 64; p.q = 3329; p.k = k;
            fill(A, k*k*64, 3329, 0, 33);
            fill(s, k*64, 3329, 0, 44);
            tt = clock();
            for (r = 0; r < reps2; r++) rmdq_mat_vec_mul_stream(A, s, out, &p);
            t = (double)(clock() - tt) / CLOCKS_PER_SEC / reps2 * 1e6;
            printf("  k=%d n=64: %.1f us\n", k, t);
        }
        p.n = 256; p.q = 3329; p.k = 2;
        fill(A, 4*256, 3329, 0, 55);
        fill(s, 2*256, 3329, 0, 66);
        reps2 = 50;
        tt = clock();
        for (r = 0; r < reps2; r++) rmdq_mat_vec_mul_stream(A, s, out, &p);
        t = (double)(clock() - tt) / CLOCKS_PER_SEC / reps2 * 1e6;
        printf("  k=2 n=256: %.1f us\n", t);
    }
    {
        /* NTT vs schoolbook, n=256 q=3329 dense */
        static int x[256], y[256], z[256];
        int r, reps3 = 200;
        double tn, ts;
        clock_t tt;
        fill(x, 256, 3329, 0, 77);
        fill(y, 256, 3329, 0, 88);
        tt = clock();
        for (r = 0; r < reps3; r++) rmdq_poly_mul_stream(x, y, z, 256, 3329);
        ts = (double)(clock() - tt) / CLOCKS_PER_SEC / reps3 * 1e6;
        tt = clock();
        for (r = 0; r < reps3; r++) rmdq_poly_mul_ntt(x, y, z, 256, 3329);
        tn = (double)(clock() - tt) / CLOCKS_PER_SEC / reps3 * 1e6;
        printf("n=256 mul: schoolbook=%.1f us ntt=%.1f us speedup=%.1fx\n", ts, tn, ts / tn);
    }
    {
        /* NTT fast vs CT twin */
        static int x[256], y[256], z[256];
        int r, reps5 = 200;
        double t1, t2;
        clock_t tt;
        fill(x, 256, 3329, 0, 101);
        fill(y, 256, 3329, 0, 102);
        tt = clock();
        for (r = 0; r < reps5; r++) rmdq_poly_mul_ntt(x, y, z, 256, 3329);
        t1 = (double)(clock() - tt) / CLOCKS_PER_SEC / reps5 * 1e6;
        tt = clock();
        for (r = 0; r < reps5; r++) rmdq_poly_mul_ntt_ct(x, y, z, 256, 3329);
        t2 = (double)(clock() - tt) / CLOCKS_PER_SEC / reps5 * 1e6;
        printf("n=256 ntt: fast=%.1f us ct=%.1f us ratio=%.2f\n", t1, t2, t2 / t1);
    }
    {
        /* mat-vec k=2 n=256: stream vs ntt */
        static int A[4*256], s[2*256], o[2*256];
        rmdq_params p;
        int r, reps4 = 50;
        double t1, t2;
        clock_t tt;
        p.n = 256; p.q = 3329; p.k = 2;
        fill(A, 4*256, 3329, 0, 55);
        fill(s, 2*256, 3329, 0, 66);
        tt = clock();
        for (r = 0; r < reps4; r++) rmdq_mat_vec_mul_stream(A, s, o, &p);
        t1 = (double)(clock() - tt) / CLOCKS_PER_SEC / reps4 * 1e6;
        tt = clock();
        for (r = 0; r < reps4; r++) rmdq_mat_vec_mul_ntt(A, s, o, &p);
        t2 = (double)(clock() - tt) / CLOCKS_PER_SEC / reps4 * 1e6;
        printf("k=2 n=256 matvec: stream=%.1f us ntt=%.1f us speedup=%.1fx\n", t1, t2, t1 / t2);
    }
    {
        /* Ahat-precomputed steady state (A transformed once, 50 vecs) */
        static int A[4*256], Ah[4*256], s[2*256], o[2*256];
        rmdq_params p;
        int r, reps6 = 50, t;
        double t1, t2;
        clock_t tt;
        p.n = 256; p.q = 3329; p.k = 2;
        fill(A, 4*256, 3329, 0, 55);
        for (t = 0; t < 4*256; t++) Ah[t] = A[t];
        rmdq_ntt_batch_fwd(Ah, 4);
        fill(s, 2*256, 3329, 0, 66);
        tt = clock();
        for (r = 0; r < reps6; r++) {
            fill(s, 2*256, 3329, 0, (unsigned)(66 + r));
            rmdq_mat_vec_mul_ntt(A, s, o, &p);
        }
        t1 = (double)(clock() - tt) / CLOCKS_PER_SEC / reps6 * 1e6;
        tt = clock();
        for (r = 0; r < reps6; r++) {
            fill(s, 2*256, 3329, 0, (unsigned)(66 + r));
            rmdq_mat_vec_mul_ahat(Ah, s, o, &p);
        }
        t2 = (double)(clock() - tt) / CLOCKS_PER_SEC / reps6 * 1e6;
        printf("k=2 n=256 matvec cold=%.1f us ahat-hot=%.1f us\n", t1, t2);
    }
    return 0;
}

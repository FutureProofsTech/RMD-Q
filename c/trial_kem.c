/* C-speed FO trial harness (n=256 q=3329 k=2, t=0 lattice path).
 * Full keygen + encaps + decaps with random coins per trial, sparse and CBD
 * sampling paths. Reports failures + wall time. Test-only RNG (rand()).
 * Usage: ./trial_kem <ntrials> <sparse|cbd>
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>
#include "rmdq.h"
#include "ntt.h"
#include "fips202.h"

#define N 256
#define Q 3329
#define K 2
#define ETA 2
#define WGT 192
#define ETAE 2

static void expand_A(int *A, const unsigned char *seed) {
    static const unsigned char tag[6] = {0x00,'k','e','m','-', 'a'};
    int i, j, t;
    for (i = 0; i < 2; i++) {
        for (j = 0; j < 2; j++) {
            unsigned char in[24], out[1024];
            memcpy(in, tag, 6);
            memcpy(in + 6, seed, 16);
            in[22] = (unsigned char)i; in[23] = (unsigned char)j;
            rmdq_shake128(out, 1024, in, 24);
            for (t = 0; t < 256; t++) {
                unsigned int wv = (unsigned int)out[2*t] | ((unsigned int)out[2*t+1] << 8);
                A[(i*2+j)*N+t] = (int)(wv % Q);
            }
        }
    }
}

int main(int argc, char **argv) {
    int T, cbd, trial, fails = 0;
    rmdq_params pp;
    clock_t t0;
    static int A[4*N], s[2*N], e[2*N], b[2*N];
    static int r[2*N], e1[2*N], e2[N];
    static unsigned char seed[16], coins[32], m32[32];

    if (argc != 3) { printf("usage: trial_kem <n> <sparse|cbd>\n"); return 2; }
    T = atoi(argv[1]);
    cbd = (strcmp(argv[2], "cbd") == 0);
    if (T <= 0) return 2;
    pp.n = N; pp.q = Q; pp.k = K;
    srand(0xC0FFEE);
    t0 = clock();
    for (trial = 0; trial < T; trial++) {
        /* random seeds */
        int i, j;
        unsigned char rb[512];
        unsigned char in[40];
        for (i = 0; i < 16; i++) seed[i] = (unsigned char)(rand() & 0xFF);
        expand_A(A, seed);
        /* s sparse (assumption), e per path */
        for (i = 0; i < 2; i++) {
            for (j = 0; j < 16; j++) in[j] = (unsigned char)(rand() & 0xFF);
            in[14] = 0; in[15] = (unsigned char)i;
            rmdq_shake128(rb, 512, in, 16);
            rmdq_sample_sparse_rb(rb, 512, N, Q, ETA, WGT, s + i * N);
            if (cbd) {
                rmdq_shake128(rb, 128, in, 16);
                rmdq_cbd(rb, N, ETAE, Q, e + i * N);
            } else {
                rmdq_shake128(rb, 512, in, 16);
                rmdq_sample_sparse_rb(rb, 512, N, Q, ETAE, N, e + i * N);
            }
        }
        RMDQ_MATVEC_NTT(A, s, b, &pp);
        for (i = 0; i < 2 * N; i++) { int t = b[i] + e[i]; if (t >= Q) t -= Q; b[i] = t; }
        /* message + encaps */
        for (i = 0; i < 32; i++) m32[i] = (unsigned char)(rand() & 0xFF);
        {
            unsigned char cin[80];
            memcpy(cin, "\x01kem-coins", 10);
            memcpy(cin + 10, m32, 32);
            /* pk_hash shortcut: hash b (test-only simplification, documented) */
            for (i = 0; i < 2 * N; i++) cin[42 + (i % 32)] ^= (unsigned char)(b[i] & 0xFF);
            rmdq_shake256(coins, 32, cin, 74);
        }
        {
            int AT[4*N], uu[2*N], vv[N], su[N], mp[N];
            unsigned char mrec[32];
            /* transpose */
            for (i = 0; i < 2; i++)
                for (j = 0; j < 2; j++)
                    memcpy(AT + (i * 2 + j) * N, A + (j * 2 + i) * N, N * sizeof(int));
            /* sample r/e1/e2 */
            for (i = 0; i < 2; i++) {
                unsigned char rin[34];
                memcpy(rin, coins, 32); rin[32] = 0; rin[33] = (unsigned char)i;
                if (cbd) {
                    unsigned char rrb[128];
                    rmdq_shake128(rrb, 128, rin, 34);
                    rmdq_cbd(rrb, N, ETA, Q, r + i * N);
                } else {
                    unsigned char rrb[512];
                    rmdq_shake128(rrb, 512, rin, 34);
                    rmdq_sample_sparse_rb(rrb, 512, N, Q, ETA, WGT, r + i * N);
                }
                memcpy(rin, coins, 32); rin[32] = 1; rin[33] = (unsigned char)i;
                if (cbd) {
                    unsigned char rrb[128];
                    rmdq_shake128(rrb, 128, rin, 34);
                    rmdq_cbd(rrb, N, ETAE, Q, e1 + i * N);
                } else {
                    unsigned char rrb[512];
                    rmdq_shake128(rrb, 512, rin, 34);
                    rmdq_sample_sparse_rb(rrb, 512, N, Q, ETAE, N, e1 + i * N);
                }
            }
            {
                unsigned char ein[34];
                memcpy(ein, coins, 32); memcpy(ein + 32, "e2", 2);
                if (cbd) {
                    unsigned char rrb[128];
                    rmdq_shake128(rrb, 128, ein, 34);
                    rmdq_cbd(rrb, N, ETAE, Q, e2);
                } else {
                    unsigned char rrb[512];
                    rmdq_shake128(rrb, 512, ein, 34);
                    rmdq_sample_sparse_rb(rrb, 512, N, Q, ETAE, N, e2);
                }
            }
            RMDQ_MATVEC_NTT(AT, r, uu, &pp);
            for (i = 0; i < 2 * N; i++) { int t = uu[i] + e1[i]; if (t >= Q) t -= Q; uu[i] = t; }
            {
                int p1[N], p2[N], msgpoly[N];
                RMDQ_NTT(b, r, p1, N, Q);
                RMDQ_NTT(b + N, r + N, p2, N, Q);
                for (i = 0; i < N; i++) {
                    int t = p1[i] + p2[i];
                    if (t >= Q) t -= Q;
                    int bit = (m32[(i / 8) % 32] >> (i % 8)) & 1;
                    msgpoly[i] = bit ? Q / 2 : 0;
                    t += e2[i]; if (t >= Q) t -= Q;
                    t += msgpoly[i]; if (t >= Q) t -= Q;
                    vv[i] = t;
                }
            }
            /* decaps */
            {
                int p1[N], p2[N];
                memset(mrec, 0, 32);
                RMDQ_NTT(s, uu, p1, N, Q);
                RMDQ_NTT(s + N, uu + N, p2, N, Q);
                for (i = 0; i < N; i++) {
                    int t = p1[i] + p2[i];
                    if (t >= Q) t -= Q;
                    su[i] = t;
                }
                rmdq_poly_sub(vv, su, mp, N, Q);
                for (i = 0; i < N; i++) {
                    int c = mp[i];
                    int d0 = c <= Q / 2 ? c : Q - c;
                    int d1 = abs(c - Q / 2);
                    if ((d0 < d1) ? 0 : 1) mrec[(i / 8) % 32] |= (unsigned char)(1 << (i % 8));
                }
                if (memcmp(mrec, m32, 32) != 0) fails++;
            }
        }
        if ((trial + 1) % 1000 == 0) { printf("... %d\n", trial + 1); fflush(stdout); }
    }
    {
        double secs = (double)(clock() - t0) / CLOCKS_PER_SEC;
        printf("%s trials=%d fails=%d (%.2f ms/trial)\n",
               cbd ? "cbd" : "sparse", T, fails, secs * 1000.0 / T);
        if (fails == 0) {
            double logup = 0.0 - 0.0;
            double up = 1.0;
            int k;
            /* CP upper 1-(1-.95)^(1/T) via log */
            up = 1.0 - exp(log(0.05) / T);
            logup = log(up) / log(2.0);
            (void)k;
            printf("95%% CP upper ~2^%.1f\n", logup);
        }
    }
    return fails ? 1 : 0;
}

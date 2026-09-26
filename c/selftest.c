/* Self-test: cross-checks C ring ops against hardcoded Python-generated vectors.
 * Build: gcc -std=c90 -Wall -Wextra -O2 -o selftest selftest.c rmdq.c ntt.c && ./selftest
 */
#include <stdio.h>
#include "rmdq.h"
#include "ntt.h"

static int fails = 0;
#define CHECK(cond, msg) do { if (!(cond)) { printf("FAIL %s\n", msg); fails++; } } while (0)

int main(void) {
    /* n=4, q=17, (1+2x) * (3+4x) mod X^4+1 = 3+10x+8x^2+... (verify by hand via python) */
    int a[4] = {1, 2, 0, 0};
    int b[4] = {3, 4, 0, 0};
    int out[4] = {0, 0, 0, 0};
    int add[4], sub[4];
    rmdq_params p;
    int A[16], s[4], r[4];
    int i;

    rmdq_poly_mul(a, b, out, 4, 17);
    /* (1*3)=3, (1*4+2*3)=10, (2*4)=8 */
    CHECK(out[0]==3 && out[1]==10 && out[2]==8 && out[3]==0, "poly_mul basic");
    {
        int outs[4];
        int t1[16], t2[16], p1[4] = {5, 0, 16, 7}, p2[4] = {0, 9, 0, 2};
        rmdq_poly_mul(p1, p2, t1, 4, 17);
        rmdq_poly_mul_stream(p1, p2, t2, 4, 17);
        CHECK(t1[0]==t2[0]&&t1[1]==t2[1]&&t1[2]==t2[2]&&t1[3]==t2[3], "stream equiv");
        rmdq_poly_mul(a, b, outs, 4, 17);
        rmdq_poly_mul_stream(a, b, out, 4, 17);
        CHECK(out[0]==3 && out[1]==10, "stream basic");
        {
            int cto[4];
            rmdq_poly_mul_ct(p1, p2, cto, 4, 17);
            CHECK(cto[0]==t1[0]&&cto[1]==t1[1]&&cto[2]==t1[2]&&cto[3]==t1[3], "ct equiv");
        }
    }

    rmdq_poly_add(a, b, add, 4, 17);
    CHECK(add[0]==4 && add[1]==6, "poly_add");
    rmdq_poly_sub(b, a, sub, 4, 17);
    CHECK(sub[0]==2 && sub[1]==2, "poly_sub");

    CHECK(rmdq_norm_inf(b, 4, 17)==4, "norm_inf");
    CHECK(rmdq_weight(a, 4)==2, "weight");

    /* mat-vec k=1: A=[1+x], s=[1+16x] (16=-1), q=17 */
    p.n=4; p.q=17; p.k=1; p.eta=1; p.w=4; p.eta_e=1; p.t=2;
    for (i=0;i<16;i++) A[i]=0;
    A[0]=1; A[1]=1;
    s[0]=1; s[1]=16; s[2]=0; s[3]=0;
    rmdq_mat_vec_mul(A, s, r, &p);
    /* (1+x)(1-x)=1-x^2 */
    CHECK(r[0]==1 && r[1]==0 && r[2]==16 && r[3]==0, "mat_vec");
    {
        int r2[4];
        int A2[16], s2[8];
        rmdq_mat_vec_mul_stream(A, s, r2, &p);
        CHECK(r2[0]==r[0]&&r2[1]==r[1]&&r2[2]==r[2]&&r2[3]==r[3], "mat_vec_stream equiv");
        /* k=2 small cross-check vs non-stream */
        {
            rmdq_params p2;
            int o1[8], o2[8], o3[8], k;
            p2.n=4; p2.q=17; p2.k=2;
            for (k=0;k<16;k++) A2[k]=(k*3+1)%17;
            for (k=0;k<8;k++) s2[k]=(k*5+2)%17;
            rmdq_mat_vec_mul(A2, s2, o1, &p2);
            rmdq_mat_vec_mul_stream(A2, s2, o2, &p2);
            rmdq_mat_vec_mul_ct(A2, s2, o3, &p2);
            CHECK(o1[0]==o2[0]&&o1[3]==o2[3]&&o1[7]==o2[7], "mat_vec_stream k=2");
            CHECK(o3[0]==o1[0]&&o3[3]==o1[3]&&o3[7]==o1[7], "mat_vec_ct k=2");
        }
    }

    /* MQ eval: eq0: 2*x0 + 3*x1*x2 ; eq1: 5*x3 (linear) ; s=(1,2,3,4), q=17 */
    {
        int triples[4*3];
        int off[2], len[2], sf[4], mout[2];
        triples[0]=2; triples[1]=0; triples[2]=-1;
        triples[3]=3; triples[4]=1; triples[5]=2;
        triples[6]=5; triples[7]=3; triples[8]=-1;
        off[0]=0; len[0]=2; off[1]=2; len[1]=1;
        sf[0]=1; sf[1]=2; sf[2]=3; sf[3]=4;
        rmdq_mq_eval(triples, off, len, 2, sf, 4, 17, mout);
        CHECK(mout[0]==(2*1+3*2*3)%17 && mout[1]==(5*4)%17, "mq_eval");
    }
    /* scalar mul */
    {
        int sc[4];
        rmdq_poly_scalar_mul(a, 3, sc, 4, 17);
        CHECK(sc[0]==3 && sc[1]==6, "scalar_mul");
    }
    /* CBD eta=2: bits [1,1,0,0] -> d=2 ; bits [0,0,1,1] -> d=-2=15 mod 17 */
    {
        unsigned char b1[1] = {0x03}, b2[1] = {0x0C}, b3[2] = {0xFF, 0xFF};
        int o1[1], o2[1], o4[4], k;
        rmdq_cbd(b1, 1, 2, 17, o1);
        rmdq_cbd(b2, 1, 2, 17, o2);
        CHECK(o1[0]==2 && o2[0]==15, "cbd basic");
        rmdq_cbd(b3, 4, 2, 17, o4);
        for (k = 0; k < 4; k++) if (o4[k] != 0) break;
        CHECK(k == 4, "cbd all-ones zero");
    }
    /* NTT (q=3329 n=256): equivalence vs schoolbook on LCG vectors */
    {
        static int x[256], y[256], r1[256], r2[256], f[256], g[256];
        unsigned s = 12345;
        int t, bad = 0;
        for (t = 0; t < 256; t++) {
            s = s * 1103515245u + 12345u;
            x[t] = (int)((s >> 8) % 3329u);
            s = s * 1103515245u + 12345u;
            y[t] = (int)((s >> 8) % 3329u);
        }
        rmdq_poly_mul_stream(x, y, r1, 256, 3329);
        rmdq_poly_mul_ntt(x, y, r2, 256, 3329);
        for (t = 0; t < 256; t++) if (r1[t] != r2[t]) { bad = 1; break; }
        CHECK(!bad, "ntt equiv schoolbook");
        /* fwd/inv roundtrip */
        for (t = 0; t < 256; t++) f[t] = x[t];
        rmdq_ntt_fwd(f);
        for (t = 0; t < 256; t++) g[t] = f[t];
        rmdq_ntt_inv(g);
        bad = 0;
        for (t = 0; t < 256; t++) if (g[t] != x[t]) { bad = 1; break; }
        CHECK(!bad, "ntt roundtrip");
    }
    /* NTT mat-vec (k=2 n=256 q=3329) vs stream */
    {
        static int A[4*256], s[2*256], o1[2*256], o2[2*256];
        rmdq_params p2;
        unsigned s2 = 999;
        int t, bad = 0;
        p2.n = 256; p2.q = 3329; p2.k = 2;
        for (t = 0; t < 4*256; t++) { s2 = s2 * 1103515245u + 12345u; A[t] = (int)((s2 >> 8) % 3329u); }
        for (t = 0; t < 2*256; t++) { s2 = s2 * 1103515245u + 12345u; s[t] = (int)((s2 >> 8) % 3329u); }
        rmdq_mat_vec_mul_stream(A, s, o1, &p2);
        rmdq_mat_vec_mul_ntt(A, s, o2, &p2);
        for (t = 0; t < 2*256; t++) if (o1[t] != o2[t]) { bad = 1; break; }
        CHECK(!bad, "ntt matvec equiv");
    }    /* CT-NTT matvec twin */
    {
        static int A[4*256], s[2*256], o1[2*256], o2[2*256];
        rmdq_params p2;
        unsigned s2 = 31337;
        int t, bad = 0;
        p2.n = 256; p2.q = 3329; p2.k = 2;
        for (t = 0; t < 4*256; t++) { s2 = s2 * 1103515245u + 12345u; A[t] = (int)((s2 >> 8) % 3329u); }
        for (t = 0; t < 2*256; t++) { s2 = s2 * 1103515245u + 12345u; s[t] = (int)((s2 >> 8) % 3329u); }
        rmdq_mat_vec_mul_ntt(A, s, o1, &p2);
        rmdq_mat_vec_mul_ntt_ct(A, s, o2, &p2);
        for (t = 0; t < 2*256; t++) if (o1[t] != o2[t]) { bad = 1; break; }
        CHECK(!bad, "ntt matvec ct equiv");
    }
    /* Ahat-precomputed matvec */
    {
        static int A[4*256], Ah[4*256], s[2*256], o1[2*256], o2[2*256];
        rmdq_params p2;
        unsigned s2 = 4242;
        int t, bad = 0;
        p2.n = 256; p2.q = 3329; p2.k = 2;
        for (t = 0; t < 4*256; t++) { s2 = s2 * 1103515245u + 12345u; A[t] = (int)((s2 >> 8) % 3329u); }
        for (t = 0; t < 2*256; t++) { s2 = s2 * 1103515245u + 12345u; s[t] = (int)((s2 >> 8) % 3329u); }
        for (t = 0; t < 4*256; t++) Ah[t] = A[t];
        rmdq_ntt_batch_fwd(Ah, 4);
        rmdq_mat_vec_mul_ntt(A, s, o1, &p2);
        rmdq_mat_vec_mul_ahat(Ah, s, o2, &p2);
        for (t = 0; t < 2*256; t++) if (o1[t] != o2[t]) { bad = 1; break; }
        CHECK(!bad, "ahat matvec equiv");
    }
    /* CT-NTT twins: identical outputs to branching versions (LCG vectors) */
    {
        static int x[256], y[256], a[256], b[256], c[256];
        unsigned s = 777;
        int t, bad = 0;
        for (t = 0; t < 256; t++) {
            s = s * 1103515245u + 12345u;
            x[t] = (int)((s >> 8) % 3329u);
            s = s * 1103515245u + 12345u;
            y[t] = (int)((s >> 8) % 3329u);
        }
        for (t = 0; t < 256; t++) { a[t] = x[t]; b[t] = x[t]; }
        rmdq_ntt_fwd(a);
        rmdq_ntt_fwd_ct(b);
        for (t = 0; t < 256; t++) if (a[t] != b[t]) { bad = 1; break; }
        CHECK(!bad, "ntt fwd ct equiv");
        rmdq_ntt_inv(a);
        rmdq_ntt_inv_ct(b);
        for (t = 0; t < 256; t++) if (a[t] != b[t] || a[t] != x[t]) { bad = 1; break; }
        CHECK(!bad, "ntt inv ct equiv+roundtrip");
        rmdq_poly_mul_ntt(x, y, a, 256, 3329);
        rmdq_poly_mul_ntt_ct(x, y, b, 256, 3329);
        for (t = 0; t < 256; t++) if (a[t] != b[t]) { bad = 1; break; }
        CHECK(!bad, "ntt mul ct equiv");
        for (t = 0; t < 256; t++) c[t] = 0;
        rmdq_poly_mul_ntt_ct(x, y, c, 16, 17); /* fallback path == schoolbook ct */
        rmdq_poly_mul_ct(x, y, b, 16, 17);
        for (t = 0; t < 16; t++) if (c[t] != b[t]) { bad = 1; break; }
        CHECK(!bad, "ntt ct fallback");
    }
    if (fails==0) printf("C SELFTEST PASSED\n");
    return fails ? 1 : 0;
}

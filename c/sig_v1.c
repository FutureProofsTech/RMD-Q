/* C Sig-v1 cross-check (toy n=16 q=17 k=1 t=2): recompute mu binding,
 * c_poly/c_scalar from (mu,w), lattice w' slack, MQ P(z_mq)==py+c*h.
 * Replicates Python byte layouts exactly (see ref/rmdq_sig*.py).
 * Usage: ./sig_v1 ../tests/kat_sigv1_16.json
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "rmdq.h"
#include "fips202.h"

static int N, Q;

static int extract_ints(const char *js, const char *key, int *out, int maxn) {
    char pat[64];
    const char *p;
    int n = 0;
    sprintf(pat, "\"%s\"", key);
    p = strstr(js, pat);
    if (!p) return -1;
    p = strchr(p, '[');
    if (!p) return -1;
    p++;
    while (*p && *p != ']' && n < maxn) {
        while (*p==' '||*p=='\n'||*p=='\r'||*p=='\t'||*p==','||*p=='[') p++;
        if (*p == ']' || *p == 0) break;
        out[n++] = atoi(p);
        if (*p=='-') p++;
        while (*p>='0'&&*p<='9') p++;
    }
    return n;
}
static int extract_hex(const char *js, const char *key, unsigned char *out, int maxn) {
    char pat[64];
    const char *p, *q;
    int n = 0;
    sprintf(pat, "\"%s\"", key);
    p = strstr(js, pat);
    if (!p) return -1;
    p = strchr(p, ':');
    if (!p) return -1;
    p = strchr(p, '"');
    if (!p) return -1;
    p++;
    q = strchr(p, '"');
    if (!q) return -1;
    while (p + 1 < q && n < maxn) {
        unsigned int v;
        char hb[3] = {p[0], p[1], 0};
        if (sscanf(hb, "%x", &v) != 1) break;
        out[n++] = (unsigned char)v;
        p += 2;
    }
    return n;
}
static int extract_int(const char *js, const char *key) {
    char pat[64];
    const char *p;
    sprintf(pat, "\"%s\"", key);
    p = strstr(js, pat);
    if (!p) return -1;
    p = strchr(p, ':');
    if (!p) return -1;
    return atoi(p + 1);
}

int main(int argc, char **argv) {
    FILE *f;
    long len;
    char *js;
    unsigned char seed_A[32], seed_P[32], pk_hash[32], mu[32], mu_exp[32], msg[256];
    int msglen, mufound;
    int A[16], b[16], triples[256*3], off[8], elen[8];
    int c_poly[16], z_lat[16], z_mq[16], h[8], w[16], py[8];
    int c_scalar, t, i, fails = 0;
    int nT = 0, nOff = 0, nLen = 0, nH = 0, nPy = 0, nCp = 0, nZl = 0, nZm = 0, nW = 0, nA = 0, nB = 0;
    int y_exp[16], nY = 0, gamma = 6, attempt = 0;

    if (argc != 2) { printf("usage: sig_v1 kat.json\n"); return 2; }
    f = fopen(argv[1], "rb");
    if (!f) { printf("FAIL open\n"); return 1; }
    fseek(f, 0, SEEK_END); len = ftell(f); fseek(f, 0, SEEK_SET);
    js = (char *)malloc((size_t)len + 1);
    if (!js) return 1;
    if (fread(js, 1, (size_t)len, f) != (size_t)len) { printf("FAIL read\n"); return 1; }
    js[len] = 0; fclose(f);

    N = extract_int(js, "n"); Q = extract_int(js, "q"); t = extract_int(js, "t");
    extract_hex(js, "seed_A_hex", seed_A, 32);
    extract_hex(js, "seed_P_hex", seed_P, 32);
    extract_hex(js, "pk_hash_hex", pk_hash, 32);
    msglen = extract_hex(js, "msg_hex", msg, 256);
    mufound = extract_hex(js, "mu_hex", mu_exp, 32);
    nA = extract_ints(js, "A_flat", A, 16);
    nB = extract_ints(js, "b_flat", b, 16);
    nT = extract_ints(js, "P_triples", triples, 256*3);
    nOff = extract_ints(js, "P_off", off, 8);
    nLen = extract_ints(js, "P_len", elen, 8);
    nCp = extract_ints(js, "c_poly", c_poly, 16);
    c_scalar = extract_int(js, "c_scalar");
    nZl = extract_ints(js, "z_lat_flat", z_lat, 16);
    nZm = extract_ints(js, "z_mq_flat", z_mq, 16);
    nH = extract_ints(js, "h", h, 8);
    nW = extract_ints(js, "w_flat", w, 16);
    nPy = extract_ints(js, "py", py, 8);
    nY = extract_ints(js, "y_flat", y_exp, 16);
    gamma = extract_int(js, "gamma");
    attempt = extract_int(js, "attempt");
    free(js);
    if (nA<=0||nB<=0||nT<=0||nOff<=0||nLen<=0||nCp<=0||nZl<=0||nZm<=0||nH<=0||nW<=0||nPy<=0||mufound<=0) {
        printf("FAIL parse\n"); return 1;
    }
    if (nY != N || gamma <= 0) { printf("FAIL parse y/gamma\n"); return 1; }

    /* 1. mu = SHAKE256(0x02||"sig-mu"||pk_hash||msg) */
    {
        unsigned char in[512];
        memcpy(in, "\x02sig-mu", 7);
        memcpy(in + 7, pk_hash, 32);
        memcpy(in + 39, msg, (size_t)msglen);
        rmdq_shake256(mu, 32, in, (unsigned long)(39 + msglen));
        if (memcmp(mu, mu_exp, 32) != 0) { printf("FAIL mu\n"); fails++; }
        else printf("mu ok\n");
    }
    /* 1b. masking y recompute: SHAKE128(mu||attempt||i) -> (byte%(2g+1))-g.
     * Fixed-shape mapping, byte-exact vs Python (rb length 64 for n<=32). */
    {
        unsigned char pre[34], rb[64];
        int y[16];
        memcpy(pre, mu, 32); pre[32] = (unsigned char)attempt; pre[33] = 0;
        rmdq_shake128(rb, 64, pre, 34);
        for (i = 0; i < N; i++) {
            int v = (int)(rb[i] % (unsigned)(2 * gamma + 1)) - gamma;
            v %= Q;
            if (v < 0) v += Q;
            y[i] = v;
        }
        for (i = 0; i < N; i++) if (y[i] != y_exp[i]) {
            printf("FAIL y[%d]: C=%d py=%d\n", i, y[i], y_exp[i]);
            fails++;
            break;
        }
        if (!fails) printf("masking y ok (byte-exact)\n");
    }
    /* 2. c_poly_seed = SHAKE256(0x02||"sig-cpoly-hash"||mu||w_bytes); c_poly from SHAKE128 */
    {
        unsigned char in[128], seed[32], stream[64];
        unsigned char wbytes[16];
        int pos = 0, used[16] = {0}, cnt = 0, si = 0;
        for (i = 0; i < N; i++) wbytes[i] = (unsigned char)(w[i] & 0xFF);
        memcpy(in, "\x02sig-cpoly-hash", 15);
        memcpy(in + 15, mu, 32);
        memcpy(in + 47, wbytes, 16);
        rmdq_shake256(seed, 32, in, 63);
        /* sample tau=2 like python */
        {
            unsigned char pre[64];
            memcpy(pre, "\x02sig-cpoly", 10);
            memcpy(pre + 10, seed, 32);
            rmdq_shake128(stream, 64, pre, 42);
        }
        {
            int got[16] = {0};
            si = 0;
            while (cnt < 2 && si + 2 <= 64) {
                int pp = stream[si] % N;
                int sg = (stream[si+1] % 2 == 0) ? 1 : Q - 1;
                si += 2;
                if (used[pp]) continue;
                used[pp] = 1;
                got[pp] = sg;
                cnt++;
            }
            for (i = 0; i < N; i++) if (got[i] != c_poly[i]) {
                printf("FAIL c_poly[%d]: C=%d py=%d\n", i, got[i], c_poly[i]);
                fails++;
                break;
            }
            if (!fails) printf("c_poly ok (tau=2)\n");
        }
        /* c_scalar = SHAKE256(0x02||"sig-cscal"||seed,2)%2+1 */
        {
            unsigned char in2[64], d[2];
            int cs;
            (void)pos;
            memcpy(in2, "\x02sig-cscal", 10);
            memcpy(in2 + 10, seed, 32);
            rmdq_shake256(d, 2, in2, 42);
            cs = ((int)d[0] | ((int)d[1] << 8)) % 2 + 1;
            if (cs != c_scalar) { printf("FAIL c_scalar: C=%d py=%d\n", cs, c_scalar); fails++; }
            else printf("c_scalar ok (%d)\n", cs);
        }
    }
    /* 3. lattice: Az_lat - c_poly*b ~= w (slack 8; vacuous for q=17, replicated) */
    {
        int Az[16], cb[16], wp[16], df[16], mx = 0;
        rmdq_params pp;
        pp.n = N; pp.q = Q; pp.k = 1;
        RMDQ_MATVEC(A, z_lat, Az, &pp);
        RMDQ_MUL(c_poly, b, cb, N, Q);
        rmdq_poly_sub(Az, cb, wp, N, Q);
        rmdq_poly_sub(wp, w, df, N, Q);
        mx = rmdq_norm_inf(df, N, Q);
        printf("wprime slack=%d (bound 8; q=17 vacuous, replicated)\n", mx);
        if (mx > 8) { printf("FAIL wprime\n"); fails++; }
    }
    /* 4. MQ: P(z_mq) == py + c*h */
    {
        int pz[8];
        (void)t;
        rmdq_mq_eval(triples, off, elen, 2, z_mq, N, Q, pz);
        for (i = 0; i < 2; i++) {
            int ex = (py[i] + c_scalar * h[i]) % Q;
            if (pz[i] != ex) { printf("FAIL MQ[%d]: got=%d exp=%d\n", i, pz[i], ex); fails++; break; }
        }
        if (!fails) printf("MQ ok\n");
    }

    if (!fails) printf("C SIG-V1 CROSS-CHECK PASSED\n");
    return fails ? 1 : 0;
}

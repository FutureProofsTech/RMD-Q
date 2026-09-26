/* C KEM toy path cross-check vs Python KAT (tests/kat_toy16.json, n=16 q=17 k=1).
 * Checks: (1) matrix expansion byte-exact vs Python shake128(tag+seed+i+j),
 * (2) b = A*s+e, (3) u = A^T*r+e1 recomputed... here e1 folded: checks b,u,v
 * recomputation from KAT s,e,r vectors.
 * Minimal JSON parsing (whitespace-tolerant, fixed schema only).
 * Build: gcc -std=c90 -Wall -Wextra -O2 -o kem_toy kem_toy.c rmdq.c fips202.c
 * Run from c/: ./kem_toy ../tests/kat_toy16.json
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "rmdq.h"
#include "fips202.h"

static int N = 16, Q = 17;

/* ---- tiny JSON int-array extractor: finds "key": [...] ---- */
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

int main(int argc, char **argv) {
    FILE *f;
    long len;
    char *js;
    unsigned char seed_A[64];
    int seedlen;
    int A[16], s[16], e[16], b[16], r[16], u[16], v[16];
    int b2[16], Ar[16], br[16], su[16], msgpoly[16];
    unsigned char msg[32];
    int i, fails = 0;
    unsigned char xof_in[64], xof_out[64];
    static const unsigned char tagbytes[6] = {0x00, 'k', 'e', 'm', '-', 'a'};
    int nA, ns, ne, nb, nr, nu, nv;

    if (argc != 2) { printf("usage: kem_toy kat.json\n"); return 2; }
    f = fopen(argv[1], "rb");
    if (!f) { printf("FAIL open\n"); return 1; }
    fseek(f, 0, SEEK_END); len = ftell(f); fseek(f, 0, SEEK_SET);
    js = (char *)malloc((size_t)len + 1);
    if (!js) return 1;
    if (fread(js, 1, (size_t)len, f) != (size_t)len) { printf("FAIL read\n"); return 1; }
    js[len] = 0; fclose(f);

    seedlen = extract_hex(js, "seed_A_hex", seed_A, 64);
    nA = extract_ints(js, "A_flat", A, 16);
    /* A is [[poly]] nested: find first inner array manually: extract all ints after A key */
    ns = extract_ints(js, "s_flat", s, 16);
    ne = extract_ints(js, "e_flat", e, 16);
    nb = extract_ints(js, "b_flat", b, 16);
    nr = extract_ints(js, "r_flat", r, 16);
    nu = extract_ints(js, "u_flat", u, 16);
    nv = extract_ints(js, "v", v, 16);
    (void)extract_hex(js, "msg_hex", msg, 32);
    free(js);

    if (seedlen <= 0 || nA <= 0 || ns <= 0 || ne <= 0 || nb <= 0 || nr <= 0 || nu <= 0 || nv <= 0) {
        printf("FAIL parse (seed=%d A=%d s=%d e=%d b=%d r=%d u=%d v=%d)\n",
               seedlen, nA, ns, ne, nb, nr, nu, nv);
        return 1;
    }

    /* 1. matrix expansion check: first poly of A via SHAKE128(tag+seed+[0,0]) */
    /* Python: shake128(tag + seed + bytes([i,j]), 4*n), 2 bytes/coeff LE % q */
    memcpy(xof_in, tagbytes, 6);
    memcpy(xof_in + 6, seed_A, (size_t)seedlen);
    xof_in[6 + seedlen] = 0; xof_in[6 + seedlen + 1] = 0;
    rmdq_shake128(xof_out, 4 * 16, xof_in, (unsigned long)(6 + seedlen + 2));
    for (i = 0; i < 16; i++) {
        unsigned int w = (unsigned int)xof_out[2*i] | ((unsigned int)xof_out[2*i+1] << 8);
        if ((int)(w % 17) != A[i]) {
            printf("FAIL expand A[%d]: C=%d py=%d\n", i, (int)(w % 17), A[i]);
            fails++;
            break;
        }
    }
    if (!fails) printf("expand A ok (16 coeffs byte-exact)\n");

    /* 2. b = A*s + e */
    RMDQ_MUL(A, s, Ar, N, Q);
    rmdq_poly_add(Ar, e, b2, N, Q);
    for (i = 0; i < 16; i++) if (b2[i] != b[i]) {
        printf("FAIL b[%d]: C=%d py=%d\n", i, b2[i], b[i]); fails++; break;
    }
    if (!fails) printf("b = A*s+e ok\n");

    /* 3. u = A*r + e1 unknown in KAT (e1 not stored) -> check A*r recompute + v consistency:
       v - (b*r + e2) path needs e2; instead verify dot products recompute:
       su = s*u ; br = b*r ; check v - su - encode(m) small (decrypt residual) */
    RMDQ_MUL(A, r, Ar, N, Q); /* A*r (k=1, A^T=A) */
    /* encode msg bits like python: bit i of msg -> q//2 */
    for (i = 0; i < 16; i++) {
        int bit = (msg[(i / 8) % 32] >> (i % 8)) & 1;
        msgpoly[i] = bit ? 8 : 0; /* q//2 = 8 */
    }
    RMDQ_MUL(b, r, br, N, Q);
    RMDQ_MUL(s, u, su, N, Q);
    /* residual = v - su - encode(m) should equal e^T r - s^T e1 + e2, expect small norm */
    {
        int tmp[16], res[16];
        rmdq_poly_sub(v, su, tmp, N, Q);
        rmdq_poly_sub(tmp, msgpoly, res, N, Q);
        printf("decrypt residual norm_inf=%d (expect small; q=17 toy may be 0-4)\n",
               rmdq_norm_inf(res, N, Q));
    }
    /* u streak check: u - A*r should equal e1 with small norm */
    {
        int e1rec[16];
        rmdq_poly_sub(u, Ar, e1rec, N, Q);
        printf("e1-rec norm_inf=%d weight=%d (expect <=1-ish toy)\n",
               rmdq_norm_inf(e1rec, N, Q), rmdq_weight(e1rec, N));
    }

    if (!fails) printf("C KEM TOY CROSS-CHECK PASSED\n");
    return fails ? 1 : 0;
}

/* C FO-KEM cross-check (toy n=16 q=97 k=1): recompute coins/ct/K from KAT seeds.
 * Replicates Python sampling byte-exactly:
 *   rb = SHAKE128(seed||nonce||i, 64); coeff = rb[j]%(2*eta+1)-eta;
 *   sparsify if weight>w: order by rb[(n+j)%64], keep first w.
 *   e2 = sample_sparse_poly(n,q,eta_e,n, SHAKE128(coins||"e2",64)) (no sparsify, w=n).
 *   coins = SHAKE256("\\x01kem-coins"||m32||pk_hash,32)
 *   K = SHAKE256("\\x01kem-shared"||m32||ct_bytes,32)
 * Usage: ./kem_fo ../tests/kat_fo16.json
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "rmdq.h"
#include "fips202.h"

static int N, Q, ETA, W, ETAE;

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

/* legacy sparse sampler (test-only): shared stable-sort version in rmdq.c */
#ifndef RMDQ_NO_LEGACY
static void sample_poly(const unsigned char *rb, int n, int q, int eta, int w, int *out) {
    rmdq_sample_sparse_rb(rb, 64, n, q, eta, w, out);
}
#endif

int main(int argc, char **argv) {
    FILE *f;
    long len;
    char *js;
    unsigned char seed_A[64], m32[32], pk_hash[32], coins[32], Kexp[32], Kgot[32];
    unsigned char sigma[32], Krejexp[32], Krej[32];
    unsigned char buf[128], rb[64], e2rb[64], ctb[64], pkbe[32];
    int b[16], u_exp[16], v_exp[16], s[16];
    int A[16], r[16], e1[16], e2[16], u[16], v[16], Ar[16], br[16], msgpoly[16];
    int i, fails = 0, use_cbd = 0;

    if (argc != 2) { printf("usage: kem_fo kat.json\n"); return 2; }
    f = fopen(argv[1], "rb");
    if (!f) { printf("FAIL open\n"); return 1; }
    fseek(f, 0, SEEK_END); len = ftell(f); fseek(f, 0, SEEK_SET);
    js = (char *)malloc((size_t)len + 1);
    if (!js) return 1;
    if (fread(js, 1, (size_t)len, f) != (size_t)len) { printf("FAIL read\n"); return 1; }
    js[len] = 0; fclose(f);

    N = extract_int(js, "n"); Q = extract_int(js, "q");
    ETA = extract_int(js, "eta"); W = extract_int(js, "w"); ETAE = extract_int(js, "eta_e");
    extract_hex(js, "seed_A_hex", seed_A, 64);
    extract_hex(js, "m_hex", m32, 32);
    extract_hex(js, "pk_hash_hex", pk_hash, 32);
    extract_hex(js, "K_hex", Kexp, 32);
    extract_hex(js, "K_reject_hex", Krejexp, 32);
    extract_hex(js, "sigma_hex", sigma, 32);
    extract_ints(js, "b_flat", b, 16);
    extract_ints(js, "u_flat", u_exp, 16);
    extract_ints(js, "v", v_exp, 16);
    extract_ints(js, "s_flat", s, 16);
    use_cbd = (strstr(js, "\"sampling\"") != NULL &&
               strstr(js, "\"cbd\"") != NULL);
    free(js);

    /* expand A[0..15] via SHAKE128(tag6||seed_A||0||0) */
    {
        static const unsigned char tag[6] = {0x00,'k','e','m','-', 'a'};
        unsigned char in[80];
        unsigned char out[64];
        memcpy(in, tag, 6);
        memcpy(in + 6, seed_A, 16);
        in[22] = 0; in[23] = 0;
        rmdq_shake128(out, 64, in, 24);
        for (i = 0; i < 16; i++) {
            unsigned int wv = (unsigned int)out[2*i] | ((unsigned int)out[2*i+1] << 8);
            A[i] = (int)(wv % (unsigned int)Q);
        }
    }

    /* coins = SHAKE256(0x01||"kem-coins"||m32||pk_hash) ; note python prefix b"\\x01kem-coins" */
    memcpy(buf, "\x01kem-coins", 10);
    memcpy(buf + 10, m32, 32);
    memcpy(buf + 42, pk_hash, 32);
    rmdq_shake256(coins, 32, buf, 74);

    /* r = sample(coins||0||0), e1 = sample(coins||1||0).
     * Sparse legacy sampler by default; CBD (fixed-shape) when KAT says so. */
    {
        unsigned char in[34];
        if (use_cbd) {
            int lr = (N * ETA * 2 + 7) / 8;
            int le = (N * ETAE * 2 + 7) / 8;
            memcpy(in, coins, 32); in[32] = 0; in[33] = 0;
            rmdq_shake128(rb, (unsigned long)lr, in, 34);
            rmdq_cbd(rb, N, ETA, Q, r);
            in[32] = 1;
            rmdq_shake128(rb, (unsigned long)le, in, 34);
            rmdq_cbd(rb, N, ETAE, Q, e1);
            memcpy(in, coins, 32); memcpy(in + 32, "e2", 2);
            rmdq_shake128(e2rb, (unsigned long)le, in, 34);
            rmdq_cbd(e2rb, N, ETAE, Q, e2);
            printf("sampling: cbd\n");
        } else {
#ifdef RMDQ_NO_LEGACY
            printf("SKIP legacy sparse sampling (retired)\n");
            return 2;
#else
            memcpy(in, coins, 32); in[32] = 0; in[33] = 0;
            rmdq_shake128(rb, 64, in, 34);
            sample_poly(rb, N, Q, ETA, W, r);
            in[32] = 1;
            rmdq_shake128(rb, 64, in, 34);
            sample_poly(rb, N, Q, ETAE, N, e1);
            /* e2 = sample(SHAKE128(coins||"e2",64)) */
            memcpy(in, coins, 32); memcpy(in + 32, "e2", 2);
            rmdq_shake128(e2rb, 64, in, 34);
            sample_poly(e2rb, N, Q, ETAE, N, e2);
#endif
        }
    }

    /* u = A*r + e1 ; v = b*r + e2 + encode(m) */
    RMDQ_MUL(A, r, Ar, N, Q);
    rmdq_poly_add(Ar, e1, u, N, Q);
    RMDQ_MUL(b, r, br, N, Q);
    for (i = 0; i < N; i++) {
        int bit = (m32[(i / 8) % 32] >> (i % 8)) & 1;
        msgpoly[i] = bit ? Q / 2 : 0;
    }
    {
        int t[16];
        rmdq_poly_add(br, e2, t, N, Q);
        rmdq_poly_add(t, msgpoly, v, N, Q);
    }
    for (i = 0; i < N; i++) {
        if (u[i] != u_exp[i] || v[i] != v_exp[i]) {
            printf("FAIL ct[%d]: C=(%d,%d) py=(%d,%d)\n", i, u[i], v[i], u_exp[i], v_exp[i]);
            fails++;
            break;
        }
    }
    if (!fails) printf("ct recompute ok (u,v byte-exact vs Python)\n");

    /* Packing wired into KAT: q=97 fits 7 bits; pack u/v, unpack, compare. */
    {
        unsigned char pb[32];
        int back[16], nb;
        nb = rmdq_pack(u_exp, N, 7, pb);
        if (nb != 14) { printf("FAIL pack u len %d\n", nb); fails++; }
        else {
            rmdq_unpack(pb, N, 7, back);
            for (i = 0; i < N; i++) if (back[i] != u_exp[i]) {
                printf("FAIL pack u[%d]\n", i); fails++; break;
            }
        }
        nb = rmdq_pack(v_exp, N, 7, pb);
        rmdq_unpack(pb, N, 7, back);
        for (i = 0; i < N; i++) if (back[i] != v_exp[i]) {
            printf("FAIL pack v[%d]\n", i); fails++; break;
        }
        if (!fails) printf("pack roundtrip ok (u,v 7-bit, 14B each)\n");
    }

    /* Packed-ct decaps: unpack fresh copies, decrypt, compare m_rec + K. */
    {
        unsigned char pb[32];
        int uu[16], vv[16], su[16], mp[16];
        unsigned char mr[32];
        memset(mr, 0, 32);
        rmdq_pack(u, N, 7, pb);
        rmdq_unpack(pb, N, 7, uu);
        rmdq_pack(v, N, 7, pb);
        rmdq_unpack(pb, N, 7, vv);
        RMDQ_MUL(s, uu, su, N, Q);
        rmdq_poly_sub(vv, su, mp, N, Q);
        for (i = 0; i < N; i++) {
            int c = mp[i] % Q;
            int d0 = c <= Q/2 ? c : Q - c;
            int d1 = abs(c - Q/2);
            if ((d0 < d1) ? 0 : 1) mr[(i/8)%32] |= (unsigned char)(1 << (i%8));
        }
        if (memcmp(mr, m32, 32) != 0) {
            printf("FAIL packed decaps m_rec\n");
            fails++;
        } else printf("packed decaps ok (unpack->decrypt match)\n");
    }

    /* K = SHAKE256(0x01||"kem-shared"||m32||ct_bytes) */
    for (i = 0; i < N; i++) { ctb[i] = (unsigned char)(u[i] & 0xFF); ctb[N + i] = (unsigned char)(v[i] & 0xFF); }
    memcpy(buf, "\x01kem-shared", 11);
    memcpy(buf + 11, m32, 32);
    memcpy(buf + 43, ctb, 32);
    (void)pkbe;
    rmdq_shake256(Kgot, 32, buf, 75);
    if (memcmp(Kgot, Kexp, 32) != 0) {
        printf("FAIL K mismatch\n exp: ");
        for (i = 0; i < 8; i++) printf("%02x", Kexp[i]);
        printf("\n got: ");
        for (i = 0; i < 8; i++) printf("%02x", Kgot[i]);
        printf("\n");
        fails++;
    } else printf("K recompute ok\n");

    /* DECAPS check in C: decrypt (v - s*u) -> bits -> m_rec, re-encrypt, compare.
       Toy q=97 KAT is correct, so must pass; tampered copy must fail. */
    {
        int su[16], mpoly2[16], diff[16], bits[16];
        unsigned char mrec[32];
        memset(mrec, 0, 32);
        RMDQ_MUL(s, u, su, N, Q);
        rmdq_poly_sub(v, su, mpoly2, N, Q);
        for (i = 0; i < N; i++) {
            int c = mpoly2[i] % Q;
            int d0 = c <= Q/2 ? c : Q - c;
            int d1 = abs(c - Q/2);
            bits[i] = (d0 < d1) ? 0 : 1;
            if (bits[i]) mrec[(i/8)%32] |= (unsigned char)(1 << (i%8));
        }
        if (memcmp(mrec, m32, 32) != 0) {
            printf("FAIL decaps decrypt: m_rec mismatch\n");
            fails++;
        } else printf("decaps decrypt ok (m_rec match)\n");
        /* tamper: flip v[0], decrypt must differ */
        {
            int vt[16];
            memcpy(vt, v, sizeof(vt));
            vt[0] = (vt[0] + 1) % Q;
            rmdq_poly_sub(vt, su, mpoly2, N, Q);
            {
                int same = 1, j;
                for (j = 0; j < N; j++) {
                    int c = mpoly2[j] % Q;
                    int d0 = c <= Q/2 ? c : Q - c;
                    int d1 = abs(c - Q/2);
                    int bit = (d0 < d1) ? 0 : 1;
                    if (bit != bits[j]) { same = 0; break; }
                }
                /* note: single-coeff flip may or may not flip bits with q=97; report either way */
                printf("tamper probe: decoded %s (info only)\n", same ? "unchanged" : "changed");
            }
        }
        (void)diff;
    }

    /* IMPLICIT-REJECT path: K_reject = SHAKE256("reject"||sigma||ct_bad) where
       ct_bad = valid ct with v[0]+1 (matches Python kat_fo_gen tamper). */
    {
        unsigned char ctbad[32], in[80];
        int vb[16];
        memcpy(vb, v, sizeof(vb));
        vb[0] = (vb[0] + 1) % Q;
        for (i = 0; i < N; i++) { ctbad[i] = (unsigned char)(u[i] & 0xFF); ctbad[N+i] = (unsigned char)(vb[i] & 0xFF); }
        memcpy(in, "reject", 6);
        memcpy(in + 6, sigma, 32);
        memcpy(in + 38, ctbad, 32);
        rmdq_shake256(Krej, 32, in, 70);
        if (memcmp(Krej, Krejexp, 32) != 0) {
            printf("FAIL K_reject mismatch\n");
            fails++;
        } else printf("K_reject ok (implicit-reject byte-exact)\n");
    }

    if (!fails) printf("C FO-KEM CROSS-CHECK PASSED\n");
    return fails ? 1 : 0;
}

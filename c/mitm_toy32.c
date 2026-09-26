/* Full MITM for noisy TOY-32 (n=32 q=97): left table wt<=3 over vars 0..15 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "rmdq.h"

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

/* combination iterator for wt out of m (indices 0..m-1), calls cb per combo */
typedef struct { int *A; int *b; int *Ptri; int *Poff; int *Plen; int *strue; long checked; long budget; int found; } Ctx;

static int gAv1[5000][32];
static int gV1[5000][32];
static int gN1 = 0;
static int gA[32], gb[32], gPtri[512*3], gPoff[8], gPlen[8], gStrue[32];

static void check_pair(const int *v1, const int *Av1, const int *v2, const int *Av2, Ctx *c) {
    int s[32], Av[32], df[32], i;
    for (i = 0; i < 32; i++) { Av[i] = Av1[i] + Av2[i]; if (Av[i] >= 97) Av[i] -= 97; }
    rmdq_poly_sub(Av, c->b, df, 32, 97);
    if (rmdq_norm_inf(df, 32, 97) > 2) return;
    for (i = 0; i < 32; i++) { s[i] = v1[i] + v2[i]; if (s[i] >= 97) s[i] -= 97; }
    {
        int mq[8];
        rmdq_mq_eval(c->Ptri, c->Poff, c->Plen, 3, s, 32, 97, mq);
        if (mq[0]==0 && mq[1]==0 && mq[2]==0) {
            int match = 1;
            for (i = 0; i < 32; i++) if (s[i] != c->strue[i]) { match = 0; break; }
            printf("BROKE match=%d checked=%ld\n", match, c->checked);
            c->found = 1;
        }
    }
}

/* enumerate right side recursively, inner loop over left table */
static int gRidx[8], gRsgn[8];
static void enum_right(int base, int start, int wt, Ctx *c) {
    int li, i;
    if (c->found || c->checked > c->budget) return;
    if (wt == 0) {
        int v2[32] = {0}, Av2[32], tmp[32];
        for (i = 0; i < 8 && gRidx[i] >= 0; i++) v2[gRidx[i]] = gRsgn[i];
        RMDQ_MUL(gA, v2, tmp, 32, 97);
        /* NOTE: A*v2 via negacyclic mul with A as poly: Av2 = A(*)v2 */
        memcpy(Av2, tmp, sizeof(Av2));
        for (li = 0; li < gN1; li++) {
            c->checked++;
            check_pair(gV1[li], gAv1[li], v2, Av2, c);
            if (c->found || c->checked > c->budget) return;
            if (c->checked % 5000000 == 0) { printf("... %ldM\n", c->checked / 1000000); fflush(stdout); }
        }
        return;
    }
    {
        int i2, s2;
        for (i2 = start; i2 < 16; i2++) {
            for (s2 = 0; s2 < 2; s2++) {
                int k;
                /* find slot */
                for (k = 0; k < 8; k++) if (gRidx[k] < 0) break;
                gRidx[k] = base + i2; gRsgn[k] = s2 ? 96 : 1;
                enum_right(base, i2 + 1, wt - 1, c);
                gRidx[k] = -1;
                if (c->found || c->checked > c->budget) return;
            }
        }
    }
}

int main(int argc, char **argv) {
    FILE *f;
    long len;
    char *js;
    long budget = 30000000L;
    Ctx c;
    int i, j, li;
    /* build all left cands wt 0..3 */
    int idx[8], sgn[8];

    if (argc < 2) { printf("usage: mitm_toy32 kat.json [budget]\n"); return 2; }
    if (argc >= 3) budget = atol(argv[2]);
    f = fopen(argv[1], "rb");
    if (!f) { printf("FAIL open\n"); return 1; }
    fseek(f, 0, SEEK_END); len = ftell(f); fseek(f, 0, SEEK_SET);
    js = (char *)malloc((size_t)len + 1);
    if (!js) return 1;
    if (fread(js, 1, (size_t)len, f) != (size_t)len) return 1;
    js[len] = 0; fclose(f);
    extract_ints(js, "A_flat", gA, 32);
    extract_ints(js, "b", gb, 32);
    extract_ints(js, "s_true", gStrue, 32);
    extract_ints(js, "P_triples", gPtri, 512*3);
    extract_ints(js, "P_off", gPoff, 8);
    extract_ints(js, "P_len", gPlen, 8);
    free(js);

    /* left table vars 0..15 */
    gN1 = 0;
    {
        int v[32] = {0};
        memcpy(gV1[gN1], v, sizeof(v));
        RMDQ_MUL(gA, v, gAv1[gN1], 32, 97);
        gN1++;
    }
    for (i = 0; i < 3 + 1; i++) { (void)i; }
    /* wt 1..3 via nested loops (simple, 16 vars) */
    {
        int a, b2, d, sa, sb, sd;
        int v[32];
        for (a = 0; a < 16; a++) for (sa = 0; sa < 2; sa++) {
            memset(v, 0, sizeof(int)*32);
            v[a] = sa ? 96 : 1;
            memcpy(gV1[gN1], v, sizeof(v));
            RMDQ_MUL(gA, v, gAv1[gN1], 32, 97);
            gN1++;
        }
        for (a = 0; a < 16; a++) for (b2 = a+1; b2 < 16; b2++)
        for (sa = 0; sa < 2; sa++) for (sb = 0; sb < 2; sb++) {
            memset(v, 0, sizeof(int)*32);
            v[a] = sa?96:1; v[b2] = sb?96:1;
            memcpy(gV1[gN1], v, sizeof(v));
            RMDQ_MUL(gA, v, gAv1[gN1], 32, 97);
            gN1++;
        }
        for (a = 0; a < 16; a++) for (b2 = a+1; b2 < 16; b2++) for (d = b2+1; d < 16; d++)
        for (sa = 0; sa < 2; sa++) for (sb = 0; sb < 2; sb++) for (sd = 0; sd < 2; sd++) {
            memset(v, 0, sizeof(int)*32);
            v[a]=sa?96:1; v[b2]=sb?96:1; v[d]=sd?96:1;
            memcpy(gV1[gN1], v, sizeof(v));
            RMDQ_MUL(gA, v, gAv1[gN1], 32, 97);
            gN1++;
            if (gN1 >= 5000) break;
        }
    }
    printf("left table %d\n", gN1);

    memset(&c, 0, sizeof(c));
    c.A = gA; c.b = gb; c.Ptri = gPtri; c.Poff = gPoff; c.Plen = gPlen; c.strue = gStrue;
    c.budget = budget;
    for (i = 0; i < 8; i++) { gRidx[i] = -1; gRsgn[i] = 0; }
    (void)idx; (void)sgn; (void)j; (void)li;
    /* right wt 0..3 over base 16 */
    for (i = 0; i <= 3; i++) {
        for (j = 0; j < 8; j++) { gRidx[j] = -1; }
        /* seed recursion: use enum_right with base=16 */
        {
            /* manual: call recursive enumerator */
            enum_right(16, 0, i, &c);
            if (c.found || c.checked > c.budget) break;
        }
    }
    printf("done checked=%ld found=%d (budget=%ld)\n", c.checked, c.found, budget);
    return c.found ? 0 : 2;
}

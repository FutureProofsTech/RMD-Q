/* Compress/decompress cross-check vs Python KAT (tests/kat_compress.json).
 * For each vector: compress in C, compare; decompress, compare vs Python
 * recomputation is implicit (roundtrip error bounded, checked in Python).
 * Usage: ./compress_test ../tests/kat_compress.json
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "rmdq.h"

int main(int argc, char **argv) {
    FILE *f;
    long len, v = 0;
    char *js;
    int fails = 0;
    const char *p;

    if (argc != 2) { printf("usage: compress_test kat.json\n"); return 2; }
    f = fopen(argv[1], "rb");
    if (!f) { printf("FAIL open\n"); return 1; }
    fseek(f, 0, SEEK_END); len = ftell(f); fseek(f, 0, SEEK_SET);
    js = (char *)malloc((size_t)len + 1);
    if (!js) return 1;
    if (fread(js, 1, (size_t)len, f) != (size_t)len) return 1;
    js[len] = 0; fclose(f);

    p = js;
    while ((p = strstr(p, "\"d\"")) != NULL) {
        int d, n, q, i;
        int poly[256], expc[256], gotc[256], rt[256];
        const char *c;
        d = atoi(strchr(p, ':') + 1);
        c = strstr(p, "\"n\"");
        n = atoi(strchr(c, ':') + 1);
        c = strstr(p, "\"q\"");
        q = atoi(strchr(c, ':') + 1);
        c = strstr(p, "\"poly\"");
        {
            const char *q2 = strchr(c, '[') + 1;
            for (i = 0; i < n; i++) {
                while (*q2==' '||*q2==',') q2++;
                poly[i] = atoi(q2);
                while (*q2=='-'||(*q2>='0'&&*q2<='9')) q2++;
            }
        }
        c = strstr(p, "\"comp\"");
        {
            const char *q2 = strchr(c, '[') + 1;
            for (i = 0; i < n; i++) {
                while (*q2==' '||*q2==',') q2++;
                expc[i] = atoi(q2);
                while (*q2=='-'||(*q2>='0'&&*q2<='9')) q2++;
            }
        }
        rmdq_compress(poly, n, d, q, gotc);
        for (i = 0; i < n; i++) if (gotc[i] != expc[i]) {
            printf("FAIL vec%ld compress[%d]: C=%d py=%d\n", v, i, gotc[i], expc[i]);
            fails++;
            break;
        }
        /* decompress self-consistency: error within roundoff bound */
        rmdq_decompress(gotc, n, d, q, rt);
        for (i = 0; i < n; i++) {
            int e = rt[i] - poly[i];
            e %= q;
            if (e < 0) e += q;
            if (e > q / 2) e = q - e;
            if (e > q / (1 << (d + 1)) + 1) {
                printf("FAIL vec%ld bound[%d]: err=%d\n", v, i, e);
                fails++;
                break;
            }
        }
        p = c + 8;
        v++;
    }
    free(js);
    if (!fails) printf("COMPRESS CROSS-CHECK PASSED (%ld vectors)\n", v);
    return fails ? 1 : 0;
}

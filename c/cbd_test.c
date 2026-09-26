/* CBD cross-check vs Python KAT (tests/kat_cbd.json).
 * Usage: ./cbd_test ../tests/kat_cbd.json
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

    if (argc != 2) { printf("usage: cbd_test kat.json\n"); return 2; }
    f = fopen(argv[1], "rb");
    if (!f) { printf("FAIL open\n"); return 1; }
    fseek(f, 0, SEEK_END); len = ftell(f); fseek(f, 0, SEEK_SET);
    js = (char *)malloc((size_t)len + 1);
    if (!js) return 1;
    if (fread(js, 1, (size_t)len, f) != (size_t)len) return 1;
    js[len] = 0; fclose(f);

    p = js;
    while ((p = strstr(p, "\"n\"")) != NULL) {
        int n, eta, q, i;
        unsigned char buf[256];
        int expect[256], got[256];
        const char *c, *h, *vend;
        int hlen;
        n = atoi(strchr(p, ':') + 1);
        c = strstr(p, "\"eta\"");
        eta = atoi(strchr(c, ':') + 1);
        c = strstr(p, "\"q\"");
        q = atoi(strchr(c, ':') + 1);
        h = strstr(p, "\"buf_hex\"");
        h = strchr(h, ':') + 1;
        while (*h == ' ' || *h == '"') h++;
        vend = strchr(h, '"');
        hlen = (int)(vend - h) / 2;
        for (i = 0; i < hlen; i++) {
            unsigned int bv;
            char hb[3] = {h[2*i], h[2*i+1], 0};
            sscanf(hb, "%x", &bv);
            buf[i] = (unsigned char)bv;
        }
        c = strstr(p, "\"poly\"");
        {
            const char *q2 = strchr(c, '[') + 1;
            for (i = 0; i < n; i++) {
                while (*q2==' '||*q2==',') q2++;
                expect[i] = atoi(q2);
                while (*q2=='-'||(*q2>='0'&&*q2<='9')) q2++;
            }
        }
        rmdq_cbd(buf, n, eta, q, got);
        for (i = 0; i < n; i++) if (got[i] != expect[i]) {
            printf("FAIL vec%ld coeff[%d]: C=%d py=%d\n", v, i, got[i], expect[i]);
            fails++;
            break;
        }
        p = vend + 1;
        v++;
    }
    free(js);
    if (!fails) printf("CBD CROSS-CHECK PASSED (%ld vectors)\n", v);
    return fails ? 1 : 0;
}

/* Pack cross-check vs Python KAT (tests/kat_pack.json).
 * For each vector: unpack Python bytes in C, compare coeffs; repack, compare bytes.
 * Usage: ./pack_test ../tests/kat_pack.json
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

    if (argc != 2) { printf("usage: pack_test kat.json\n"); return 2; }
    f = fopen(argv[1], "rb");
    if (!f) { printf("FAIL open\n"); return 1; }
    fseek(f, 0, SEEK_END); len = ftell(f); fseek(f, 0, SEEK_SET);
    js = (char *)malloc((size_t)len + 1);
    if (!js) return 1;
    if (fread(js, 1, (size_t)len, f) != (size_t)len) return 1;
    js[len] = 0; fclose(f);

    p = js;
    while ((p = strstr(p, "\"bits\"")) != NULL) {
        int bits, n, i;
        int coeffs[256], back[256];
        unsigned char packed[512], repacked[512];
        const char *c, *h;
        int nbytes, got;
        bits = atoi(strchr(p, ':') + 1);
        c = strstr(p, "\"n\"");
        n = atoi(strchr(c, ':') + 1);
        c = strstr(p, "\"coeffs\"");
        {
            const char *q = strchr(c, '[') + 1;
            for (i = 0; i < n; i++) {
                while (*q==' '||*q==',') q++;
                coeffs[i] = atoi(q);
                while (*q=='-'||(*q>='0'&&*q<='9')) q++;
            }
        }
        h = strstr(p, "\"packed_hex\"");
        h = strchr(h, ':') + 1;
        while (*h == ' ' || *h == '"') h++; /* now at hex start */
        {
            const char *vend = strchr(h, '"');
            int hlen = (int)(vend - h) / 2, k;
            for (k = 0; k < hlen; k++) {
                unsigned int bv;
                char hb[3] = {h[2*k], h[2*k + 1], 0};
                sscanf(hb, "%x", &bv);
                packed[k] = (unsigned char)bv;
            }
            nbytes = hlen;
            got = rmdq_unpack(packed, n, bits, back);
            if (got > nbytes) { printf("FAIL vec%ld overread\n", v); fails++; }
            for (i = 0; i < n; i++) if (back[i] != coeffs[i]) {
                printf("FAIL vec%ld coeff[%d]: C=%d py=%d\n", v, i, back[i], coeffs[i]);
                fails++;
                break;
            }
            {
                int nb = rmdq_pack(coeffs, n, bits, repacked);
                if (nb != nbytes || memcmp(repacked, packed, (size_t)nbytes) != 0) {
                    printf("FAIL vec%ld repack (%d vs %d bytes)\n", v, nb, nbytes);
                    fails++;
                }
            }
            p = vend + 1;
            v++;
        }
    }
    free(js);
    if (!fails) printf("PACK CROSS-CHECK PASSED (%ld vectors)\n", v);
    return fails ? 1 : 0;
}

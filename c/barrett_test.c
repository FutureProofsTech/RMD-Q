/* Exhaustive Barrett check: all x in [0,(Q-1)^2] (the exact zeta*v domain).
 * Slow (~0.5s): separate target, not part of default selftest.
 * Usage: ./barrett_test
 */
#include <stdio.h>
#include "ntt_tables.h"

#define Q 3329
#define MU 20158

int main(void) {
    long x;
    long maxcorr = 0;
    for (x = 0; x < (long)(Q - 1) * (Q - 1); x++) {
        unsigned long t = ((unsigned long)x * MU) >> 26;
        long r = x - (long)(t * Q);
        long c = 0;
        while (r >= Q) { r -= Q; c++; }
        if (r != x % Q || c > 1) {
            printf("FAIL x=%ld r=%ld exp=%ld corr=%ld\n", x, r, x % Q, c);
            return 1;
        }
        if (c > maxcorr) maxcorr = c;
    }
    (void)maxcorr;
    printf("BARRETT EXHAUSTIVE PASSED (11M products, max 1 correction)\n");
    return 0;
}

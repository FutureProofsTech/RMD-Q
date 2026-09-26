/* Keccak-f1600 reference permutation + Keccak sponge for SHAKE. C90. */
#include "fips202.h"

static unsigned long long load64(const unsigned char *x) {
    unsigned long long r = 0;
    int i;
    for (i = 0; i < 8; i++) r |= ((unsigned long long)x[i]) << (8 * i);
    return r;
}

static unsigned long long ROL(unsigned long long a, int o) {
    return (a << o) ^ (a >> (64 - o));
}

/* round constants */
static const unsigned long long RC[24] = {
    0x0000000000000001ULL, 0x0000000000008082ULL, 0x800000000000808aULL,
    0x8000000080008000ULL, 0x000000000000808bULL, 0x0000000080000001ULL,
    0x8000000080008081ULL, 0x8000000000008009ULL, 0x000000000000008aULL,
    0x0000000000000088ULL, 0x0000000080008009ULL, 0x000000008000000aULL,
    0x000000008000808bULL, 0x800000000000008bULL, 0x8000000000008089ULL,
    0x8000000000008003ULL, 0x8000000000008002ULL, 0x8000000000000080ULL,
    0x000000000000800aULL, 0x800000008000000aULL, 0x8000000080008081ULL,
    0x8000000000008080ULL, 0x0000000080000001ULL, 0x8000000080008008ULL
};
static const int RHO[24] = {
     1,  3,  6, 10, 15, 21, 28, 36, 45, 55,  2, 14,
    27, 41, 56,  8, 25, 43, 62, 18, 39, 61, 20, 44
};
static const int PI[24] = {
    10,  7, 11, 17, 18,  3,  5, 16,  8, 21, 24,  4,
    15, 23, 19, 13, 12,  2, 20, 14, 22,  9,  6,  1
};

static void keccakf(unsigned long long s[25]) {
    int round, j;
    unsigned long long t, bc[5];
    for (round = 0; round < 24; round++) {
        /* Theta */
        for (j = 0; j < 5; j++)
            bc[j] = s[j] ^ s[j+5] ^ s[j+10] ^ s[j+15] ^ s[j+20];
        for (j = 0; j < 5; j++) {
            t = bc[(j+4)%5] ^ ROL(bc[(j+1)%5], 1);
            s[j] ^= t; s[j+5] ^= t; s[j+10] ^= t; s[j+15] ^= t; s[j+20] ^= t;
        }
        /* Rho Pi */
        t = s[1];
        for (j = 0; j < 24; j++) {
            int jj = PI[j];
            bc[0] = s[jj];
            s[jj] = ROL(t, RHO[j]);
            t = bc[0];
        }
        /* Chi */
        for (j = 0; j < 25; j += 5) {
            unsigned long long a0=s[j],a1=s[j+1],a2=s[j+2],a3=s[j+3],a4=s[j+4];
            s[j]=a0^((~a1)&a2); s[j+1]=a1^((~a2)&a3); s[j+2]=a2^((~a3)&a4);
            s[j+3]=a3^((~a4)&a0); s[j+4]=a4^((~a0)&a1);
        }
        /* Iota */
        s[0] ^= RC[round];
    }
}

static void keccak_absorb_squeeze(unsigned char *out, unsigned long outlen,
                                  const unsigned char *in, unsigned long inlen,
                                  int rate, unsigned char delim) {
    unsigned long long s[25];
    unsigned char t[200];
    int i, j;
    for (i = 0; i < 25; i++) s[i] = 0;
    /* absorb full blocks */
    while (inlen >= (unsigned long)rate) {
        for (i = 0; i < rate / 8; i++) s[i] ^= load64(in + 8 * i);
        keccakf(s);
        in += rate; inlen -= rate;
    }
    /* last block + padding */
    for (i = 0; i < rate; i++) t[i] = 0;
    for (i = 0; i < (int)inlen; i++) t[i] = in[i];
    t[inlen] ^= delim;
    t[rate - 1] ^= 0x80;
    for (i = 0; i < rate / 8; i++) s[i] ^= load64(t + 8 * i);
    keccakf(s);
    /* squeeze */
    while (outlen > 0) {
        int block = outlen < (unsigned long)rate ? (int)outlen : rate;
        for (j = 0; j < block; j++) {
            /* extract byte j of state */
            out[j] = (unsigned char)((s[j / 8] >> (8 * (j % 8))));
        }
        outlen -= (unsigned long)block;
        out += block;
        if (outlen) keccakf(s);
    }
}

void rmdq_shake128(unsigned char *out, unsigned long outlen,
                   const unsigned char *in, unsigned long inlen) {
    keccak_absorb_squeeze(out, outlen, in, inlen, 168, 0x1F);
}
void rmdq_shake256(unsigned char *out, unsigned long outlen,
                   const unsigned char *in, unsigned long inlen) {
    keccak_absorb_squeeze(out, outlen, in, inlen, 136, 0x1F);
}

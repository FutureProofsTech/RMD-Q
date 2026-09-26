/* Minimal Keccak-f1600 + SHAKE128/256 one-shot (public-domain style, C90).
 * Follows FIPS 202 padding 0x1F ... 0x80, rates 168 (SHAKE128) / 136 (SHAKE256).
 * For test + embedded portability. NOT optimized.
 */
#ifndef RMDQ_FIPS202_H
#define RMDQ_FIPS202_H

void rmdq_shake128(unsigned char *out, unsigned long outlen,
                   const unsigned char *in, unsigned long inlen);
void rmdq_shake256(unsigned char *out, unsigned long outlen,
                   const unsigned char *in, unsigned long inlen);

#endif

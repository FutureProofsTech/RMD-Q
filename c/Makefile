CC=gcc
CFLAGS=-std=c90 -Wall -Wextra -O2 -Werror
all: selftest fips202_test kem_toy kem_fo sig_v1 mitm_toy32 pack_test bench cbd_test barrett_test kem256 compress_test
selftest: selftest.c rmdq.c rmdq.h ntt.c ntt.h ntt_tables.h
	$(CC) $(CFLAGS) -o selftest selftest.c rmdq.c ntt.c
fips202_test: fips202_test.c fips202.c fips202.h
	$(CC) $(CFLAGS) -o fips202_test fips202_test.c fips202.c
kem_toy: kem_toy.c rmdq.c rmdq.h fips202.c fips202.h
	$(CC) $(CFLAGS) -o kem_toy kem_toy.c rmdq.c fips202.c
kem_fo: kem_fo.c rmdq.c rmdq.h fips202.c fips202.h
	$(CC) $(CFLAGS) -o kem_fo kem_fo.c rmdq.c fips202.c
kem256: kem256.c rmdq.c rmdq.h ntt.c ntt.h ntt_tables.h fips202.c fips202.h
	$(CC) $(CFLAGS) -o kem256 kem256.c rmdq.c ntt.c fips202.c
sig_v1: sig_v1.c rmdq.c rmdq.h fips202.c fips202.h
	$(CC) $(CFLAGS) -o sig_v1 sig_v1.c rmdq.c fips202.c
mitm_toy32: mitm_toy32.c rmdq.c rmdq.h
	$(CC) $(CFLAGS) -o mitm_toy32 mitm_toy32.c rmdq.c
bench: bench.c rmdq.c rmdq.h ntt.c ntt.h ntt_tables.h
	$(CC) $(CFLAGS) -o bench bench.c rmdq.c ntt.c
pack_test: pack_test.c rmdq.c rmdq.h
	$(CC) $(CFLAGS) -o pack_test pack_test.c rmdq.c
cbd_test: cbd_test.c rmdq.c rmdq.h
	$(CC) $(CFLAGS) -o cbd_test cbd_test.c rmdq.c
barrett_test: barrett_test.c ntt_tables.h
	$(CC) $(CFLAGS) -o barrett_test barrett_test.c
trial_kem: trial_kem.c rmdq.c rmdq.h ntt.c ntt.h ntt_tables.h fips202.c fips202.h
	$(CC) $(CFLAGS) -o trial_kem trial_kem.c rmdq.c ntt.c fips202.c -lm
compress_test: compress_test.c rmdq.c rmdq.h
	$(CC) $(CFLAGS) -o compress_test compress_test.c rmdq.c
test: selftest fips202_test kem_toy kem_fo sig_v1 pack_test cbd_test barrett_test
	./selftest
	./fips202_test
	./kem_toy ../tests/kat_toy16.json
	./kem_fo ../tests/kat_fo16.json
	./kem_fo ../tests/kat_fo_cbd16.json
	./sig_v1 ../tests/kat_sigv1_16.json
	./pack_test ../tests/kat_pack.json
	./cbd_test ../tests/kat_cbd.json
	./barrett_test
	./kem256 ../tests/kat_kem256.json
	./kem256 ../tests/kat_kem256_cbd.json
	./compress_test ../tests/kat_compress.json
mitm-test: mitm_toy32
	./mitm_toy32 ../tests/kat_toy32_noisy.json 30000000
trials: trial_kem
	./trial_kem 1000 sparse
	./trial_kem 2000 cbd
no-legacy-test: selftest.c rmdq.c rmdq.h ntt.c ntt.h ntt_tables.h kem_fo.c sig_v1.c fips202.c fips202.h kem256.c cbd_test.c pack_test.c barrett_test.c
	$(CC) $(CFLAGS) -DRMDQ_NO_LEGACY -o /tmp/nl_selftest selftest.c rmdq.c ntt.c
	/tmp/nl_selftest
	$(CC) $(CFLAGS) -DRMDQ_NO_LEGACY -o /tmp/nl_kem_fo kem_fo.c rmdq.c fips202.c
	/tmp/nl_kem_fo ../tests/kat_fo_cbd16.json
	$(CC) $(CFLAGS) -DRMDQ_NO_LEGACY -o /tmp/nl_sig_v1 sig_v1.c rmdq.c fips202.c
	/tmp/nl_sig_v1 ../tests/kat_sigv1_16.json
	$(CC) $(CFLAGS) -DRMDQ_NO_LEGACY -o /tmp/nl_kem256 kem256.c rmdq.c ntt.c fips202.c
	/tmp/nl_kem256 ../tests/kat_kem256_cbd.json
	$(CC) $(CFLAGS) -DRMDQ_NO_LEGACY -o /tmp/nl_cbd cbd_test.c rmdq.c
	/tmp/nl_cbd ../tests/kat_cbd.json
	$(CC) $(CFLAGS) -DRMDQ_NO_LEGACY -o /tmp/nl_pack pack_test.c rmdq.c
	/tmp/nl_pack ../tests/kat_pack.json
	$(CC) $(CFLAGS) -DRMDQ_NO_LEGACY -o /tmp/nl_barrett barrett_test.c
	/tmp/nl_barrett
	$(CC) $(CFLAGS) -DRMDQ_NO_LEGACY -o /tmp/nl_compress compress_test.c rmdq.c
	/tmp/nl_compress ../tests/kat_compress.json
ct-test: selftest.c rmdq.c rmdq.h ntt.c ntt.h ntt_tables.h kem_fo.c sig_v1.c fips202.c fips202.h kem256.c
	$(CC) $(CFLAGS) -DRMDQ_MUL=rmdq_poly_mul_ct -DRMDQ_MATVEC=rmdq_mat_vec_mul_ct -o /tmp/ct_selftest selftest.c rmdq.c ntt.c
	/tmp/ct_selftest
	$(CC) $(CFLAGS) -DRMDQ_MUL=rmdq_poly_mul_ct -DRMDQ_MATVEC=rmdq_mat_vec_mul_ct -o /tmp/ct_kem_fo kem_fo.c rmdq.c fips202.c
	/tmp/ct_kem_fo ../tests/kat_fo16.json
	$(CC) $(CFLAGS) -DRMDQ_MUL=rmdq_poly_mul_ct -DRMDQ_MATVEC=rmdq_mat_vec_mul_ct -o /tmp/ct_sig_v1 sig_v1.c rmdq.c fips202.c
	/tmp/ct_sig_v1 ../tests/kat_sigv1_16.json
	$(CC) $(CFLAGS) -DRMDQ_NTT=rmdq_poly_mul_ntt_ct -DRMDQ_MATVEC_NTT=rmdq_mat_vec_mul_ntt_ct -o /tmp/ct_kem256 kem256.c rmdq.c ntt.c fips202.c
	/tmp/ct_kem256 ../tests/kat_kem256.json
	/tmp/ct_kem256 ../tests/kat_kem256_cbd.json
clean:
	rm -f selftest fips202_test kem_toy kem_fo sig_v1 mitm_toy32 pack_test bench cbd_test barrett_test kem256 trial_kem compress_test
sanitize:
	$(CC) -std=c90 -Wall -Wextra -O1 -g -fsanitize=address,undefined -o /tmp/san_selftest selftest.c rmdq.c ntt.c
	/tmp/san_selftest
	$(CC) -std=c90 -Wall -Wextra -O1 -g -fsanitize=address,undefined -o /tmp/san_kem kem_toy.c rmdq.c fips202.c
	/tmp/san_kem ../tests/kat_toy16.json
	$(CC) -std=c90 -Wall -Wextra -O1 -g -fsanitize=address,undefined -o /tmp/san_fo kem_fo.c rmdq.c fips202.c
	/tmp/san_fo ../tests/kat_fo16.json
	$(CC) -std=c90 -Wall -Wextra -O1 -g -fsanitize=address,undefined -o /tmp/san_sig sig_v1.c rmdq.c fips202.c
	/tmp/san_sig ../tests/kat_sigv1_16.json
	$(CC) -std=c90 -Wall -Wextra -O1 -g -fsanitize=address,undefined -o /tmp/san_cbd cbd_test.c rmdq.c
	/tmp/san_cbd ../tests/kat_cbd.json
strict:
	$(CC) -std=c90 -Wall -Wextra -Wconversion -Wpedantic -O2 -Werror -c rmdq.c -o /tmp/strict_rmdq.o
	$(CC) -std=c99 -Wall -Wextra -O2 -Werror -c fips202.c -o /tmp/strict_fips.o
	$(CC) -std=c90 -Wall -Wextra -Wconversion -Wpedantic -O2 -Werror -c ntt.c -o /tmp/strict_ntt.o
	$(CC) -std=c90 -Wall -Wextra -Wconversion -Wpedantic -O2 -Werror -o /tmp/strict_st selftest.c rmdq.c ntt.c
	/tmp/strict_st
analyze:
	$(CC) -std=c90 -O2 -fanalyzer -c rmdq.c -o /tmp/an_rmdq.o
	$(CC) -std=c90 -O2 -fanalyzer -c fips202.c -o /tmp/an_fips.o
	$(CC) -std=c90 -O2 -fanalyzer -c kem_fo.c -o /tmp/an_fo.o
	$(CC) -std=c90 -O2 -fanalyzer -c sig_v1.c -o /tmp/an_sig.o
timing-smoke:
	$(CC) -std=c90 -O2 -c ntt.c -o /tmp/ts_ntt.o
	@./timing_smoke.sh /tmp/ts_ntt.o
m4-check:
	arm-none-eabi-gcc -std=c90 -mcpu=cortex-m4 -mthumb -Os -Wall -Wextra -Werror -c rmdq.c -o /tmp/m4_rmdq.o
	arm-none-eabi-gcc -std=c99 -mcpu=cortex-m4 -mthumb -Os -Wall -Wextra -Werror -c fips202.c -o /tmp/m4_fips.o
	arm-none-eabi-gcc -std=c90 -mcpu=cortex-m4 -mthumb -Os -Wall -Wextra -Werror -c ntt.c -o /tmp/m4_ntt.o
	arm-none-eabi-size /tmp/m4_rmdq.o /tmp/m4_fips.o /tmp/m4_ntt.o

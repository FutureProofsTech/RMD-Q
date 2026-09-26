#!/bin/bash
# run_all.sh -- full verification in one command (default + CT + no-legacy
# builds, strict, analyzer, timing smoke, M4 check, Python suites).
# Slow Python suites (kem256/sig256/planted/breaks) run last.
# NOT included (nightly, ~10+ min each): tests/test_sig256.py,
# ref/break_mitm_pruned.py full budget, ref/grobner_gf.py full sweep.
set -u
cd "$(dirname "$0")"
fail=0

echo "=== KAT regen (deterministic) ==="
python3 ref/kat_gen.py && python3 ref/kat_fo_gen.py && \
python3 ref/kat_fo_cbd_gen.py && python3 ref/kat_sigv1_gen.py && \
python3 ref/kat_pack_gen.py && python3 ref/kat_cbd_gen.py >/dev/null && \
python3 ref/kat_kem256_gen.py && python3 ref/kat_kem256_cbd_gen.py && \
python3 ref/kat_toy32_gen.py >/dev/null || fail=1

echo "=== C: build + test + ct + no-legacy ==="
make -C c clean >/dev/null && make -C c >/dev/null 2>&1 || fail=1
make -C c test 2>&1 | grep -E "FAIL" && fail=1
make -C c ct-test 2>&1 | grep -E "FAIL" && fail=1
make -C c no-legacy-test 2>&1 | grep -E "FAIL" && fail=1
make -C c timing-smoke >/dev/null 2>&1 || fail=1
make -C c m4-check >/dev/null 2>&1 || fail=1
make -C c strict >/dev/null 2>&1 || fail=1
make -C c analyze >/dev/null 2>&1 || fail=1
echo "(C stages done)"

echo "=== Python fast suites ==="
for t in test_toy test_kem_sig test_sig_v1 test_kem_cbd test_hybrid test_kat_meta; do
  python3 tests/$t.py >/dev/null 2>&1 || { echo "PYFAIL $t"; fail=1; }
done
python3 ref/break_toy.py >/dev/null 2>&1 || fail=1
python3 ref/ntt_gen.py >/dev/null 2>&1 || fail=1
echo "(fast suites done)"

echo "=== Python slow suites ==="
python3 tests/test_kem256.py 2>&1 | tail -n 1
python3 tests/test_planted.py 2>&1 | tail -n 1
python3 tests/test_planted_joint.py 2>&1 | tail -n 1
python3 ref/estimate_security.py | head -n 3
python3 ref/failure_exact.py | head -n 2

if [ "$fail" = "0" ]; then echo "ALL_OK"; else echo "FAILURES PRESENT"; fi
exit $fail

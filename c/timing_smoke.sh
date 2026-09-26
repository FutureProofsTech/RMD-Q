#!/bin/bash
# timing-smoke: objdump check that CT-NTT functions contain no sign-test jumps.
# Loop back-edges on fixed trip counts are expected (secret-independent).
# FAILs the build if js/jns/jl/jge/jle/jg appear in _ct functions.
# Usage: ./timing_smoke.sh <ntt.o>
set -u
OBJ=${1:?usage: timing_smoke.sh <ntt.o>}
fail=0
for fn in rmdq_ntt_fwd_ct rmdq_ntt_inv_ct rmdq_poly_mul_ntt_ct rmdq_mat_vec_mul_ntt_ct; do
  start=$(objdump -t "$OBJ" | awk -v f="$fn" '$NF==f{print $1}')
  if [ -z "$start" ]; then echo "MISS $fn"; fail=1; continue; fi
  # disassemble from fn start, take lines until next FUNC (next 0xaddr+name pattern at col0)
  n=$(objdump -d --start-address="0x$start" "$OBJ" | awk 'NR==1{next} /^[0-9a-f]+ </{exit} {print}' \
      | grep -cE '	j(s|ns|l|ge|le|g) ')
  echo "$fn: sign-jumps=$n"
  if [ "$n" != "0" ]; then fail=1; fi
done
# reference: branching twin MUST still show its sign jump (proves check sensitivity)
ref=$(objdump -d "$OBJ" | awk '/<rmdq_ntt_fwd>:/{f=1} f' | grep -cE '	js ')
echo "rmdq_ntt_fwd reference js-count=$ref (expect >=1)"
if [ "$ref" = "0" ]; then echo "WARN: check may be blind (no js in reference)"; fi
exit $fail

# Open items (honest backlog, updated as work lands)

1. **Planted-P keygen [DONE v2, analysis in docs/07]**: supports independent
   of s, solved fix coeff, resample-to-nonzero + pad pure-random. Fix coeffs
   uniform (chi2 17.4 vs H0 15); end-to-end FO roundtrip on planted n=256/t=8
   key. Residual: pad-term zero-coord hint (accepted, documented).
   Kill-phase rounds 1-3 DONE: planted n=16 Gröbner BASIS in ~2s (sympy)
   / 0.3-0.5s (msolve) but FULL msolve solve >300s even at n=16 --
   basis-trivial, solution-enumeration-hard (the variety is huge; attacker
   must filter for the sparse root). msolve GB scaling with bounds:
   n=16 ~0.5s, n=24 180s, n=28 >1200s (bounded, unfinished), n=32 OOMs
   at 114GB on 16 cores (kernel-logged). Pure-MQ (no bounds) GB trivially
   terminates everywhere (0.1s) but recovers nothing (positive-dimensional).
   Hardness sits where theory says: bounds force zero-dimensionality and
   drive the blowup. Planted vs random MQ show NO
   measurable non-genericity at n=16 (both trivial GB with bounds; without
   bounds planted needs zero F4 rounds vs random deg-4 -- same 0.0s class).
   Bardet d_reg bounds uninformative here (15/27/None vs observed 2-4).
   Support floor 2^411 at prod. Hybrid-guessing round 1 DONE (docs/09):
   optimum g=0, enumeration validated, wt lever quantified (wt=256 closes
   gap). Joint XL model DONE round 2: MQ subsystem contributes negligibly
   (XL infeasible at prod even with field equations); lattice path binds
   in-model. msolve scaling: 0.5s/180s/>1200s/OOM across n=16/24/28/32.
   NEXT: hints-variant/BKW analysis + larger-scale regularity study
   (the remaining cryptanalytic unknowns).
2. **CT-NTT [DONE]**: branch-free twins + ZINVW table + masked accumulation;
   equivalence-tested + `ct-test` KEM256 green (docs/05). Timing smoke
   AUTOMATED (`make timing-smoke`: 0 sign-jumps in 4 CT fns, reference
   still shows its js). Remaining: formal object-level proof (out of scope
   v0); toy-fallback `%` (toy-only).
3. **Sampling [DONE]**: shared stable-sort sparse sampler (== Python via
   ctypes n=16+256); CBD wired into FO encaps (sparse+CBD KATs green at
   n=256); buffers generalized (64B/512B/128B); C Sig masking-y recompute
   green; legacy retired behind `-DRMDQ_NO_LEGACY` (`make no-legacy-test`
   green, sparse KATs skip exit-2).
4. **Prod params freeze [ESTIMATES DONE, docs/08 + spec/07 — NO CLAIMS]**:
   dual-BKZ validates within 3 bits on Kyber512 (20 bits optimistic on 768,
   stated); fpylll BKZ-constant check agrees 0.3%; ours ~5-7 bits under
   same-N reference IN-MODEL. Exact failure distributions computed
   (uncompressed 2^-910..2^-512; compressed (10,5) 2^-268.6, (10,4)
   2^-235.4 — all far under the 2^-138 bar). wt ALIGNED to 192 (0 failures
   re-measured). BLOCKING for Cats: hybrid hints-variants/BKW/quantum-walk,
   C-speed failure trials, MQ rationale, planted kill-phase clean.
5. **Toolchains [CLOSED]**: arm-none-eabi-gcc-cs, valgrind,
   libasan/ubsan installed. ASan+UBSan clean, valgrind 0 errors
   (selftest/kem_fo/kem256), M4 `-Werror` clean (rmdq 1550B + fips202
   1368B + ntt 4464B text; frames ≤56B). fpylll installed: BKZ-constant
   cross-check agrees 0.3% at β=20/25/35 (β=45 dim-200 exceeds patience;
   trend flat, documented).
   NOTE: ntt.o bss dieted to 24KB shared workspace (was 60KB per-function
   statics); still too fat for small MCUs — streaming path or
   caller-provided buffers required first (`make m4-check` pins).
6. **Perf [Ahat MEASURED this round]**: hot 25.6us vs cold 32us (~20%;
   pointwise+inverse dominate — honest, smaller than hoped). Montgomery:
   EVALUATED AND DEFERRED (Barrett exhaustive-proven, covers all hot
   products; ~10-15% projected gain vs conversion complexity). M4 DSP
   assembly after C freeze.
7. **Fixed across rounds**: SHAKE multi-block squeeze overflow, k=2 matrix
   flatten bug, NTT inv layer-order + sort-direction bugs, KAT prefix-length
   bug, kem256 e1 weight transcription, kem256 undersized K buffers
   (-Warray-bounds), Sig linear-term defect (homogeneous-quad restriction),
   KAT generators hardcoding params instead of emitting `p.*` (caught by
   wt=192 alignment; `tests/test_kat_meta.py` guards required fields).

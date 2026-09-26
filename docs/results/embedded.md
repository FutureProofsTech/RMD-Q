# Results: Embedded suitability (Cortex-M class)

Reproduce: `make -C c m4-check` (needs `arm-none-eabi-gcc`).

## Footprint (Cortex-M4, `-Os`, `-Werror` clean)

| Object | text | bss |
|--------|------|-----|
| `rmdq.o` (ring, sampling, codec) | 1550 B | 0 |
| `fips202.o` (SHAKE) | 1368 B | 0 |
| `ntt.o` (NTT backend) | 4464 B | 24 KB shared static |
| **Crypto core total** | **≈3.9 KB** | — |

Stack frames: primitives ≤ 56 B; matrix-vector ≈ 1100 B locals. No malloc,
no float, strict C90 core (Keccak needs C99 `uint64_t`, universal practice).

## The 24 KB honesty note

`ntt.o` bss was 60 KB of per-function statics — dieted to one 24 KB shared
workspace (single-threaded). Still too fat for small MCUs: the streaming
schoolbook path (O(1) extra stack, 37–38× smaller frames) is the embedded
story until buffers become caller-provided. Both backends coexist with
automatic fallback.

## Execution evidence status

- Static: sizes, frames, Thumb-2 disassembly with single-cycle hardware
  multiplies in hot loops — all measured on the M4 target triple.
- Not available on site: bare-metal execution (qemu-arm can't run M-profile
  firmware; no hardware), M4 cycle counts (projections in
  `ref/m4_cycles.py` only), power measurements.

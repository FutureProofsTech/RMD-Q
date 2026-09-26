"""KAT metadata guard: every KAT consumed by C must carry the params C parses.
Regressions caught: hardcoded fields drifting from generation params."""
import json
import os

DIR = os.path.join(os.path.dirname(__file__))

REQUIRED = {
    "kat_kem256.json": ["n", "q", "k", "eta", "w", "eta_e", "K_reject_hex"],
    "kat_kem256_cbd.json": ["n", "q", "k", "eta", "w", "eta_e", "sampling", "K_reject_hex"],
    "kat_fo16.json": ["n", "q", "k", "eta", "w", "eta_e", "K_reject_hex"],
    "kat_fo_cbd16.json": ["n", "q", "k", "eta", "w", "eta_e", "sampling", "K_reject_hex"],
    "kat_sigv1_16.json": ["n", "q", "k", "y_flat", "gamma", "attempt"],
    "kat_toy16.json": ["n", "q", "k"],
    "kat_toy32_noisy.json": ["n", "q"],
}


def test_kat_meta():
    for fn, keys in REQUIRED.items():
        with open(os.path.join(DIR, fn)) as f:
            kat = json.load(f)
        missing = [k for k in keys if k not in kat]
        assert not missing, f"{fn} missing {missing}"
    print("KAT metadata ok")


if __name__ == "__main__":
    test_kat_meta()

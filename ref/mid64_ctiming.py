"""MID-64 C timing projection from measured mat_vec_stream rates."""
import sys
sys.path.insert(0, "ref")

def main():
    # Measured (portable C, O2, x86_64): k=2 n=64 mat_vec 12.7us; k=2 n=256 198.7us.
    # KEM keygen ~ k^2 expands + k mat-vec; encaps ~ 2 mat-vec; decaps ~ 1 + re-encrypt 2.
    # SHAKE expands dominate at small n; sampling ~ O(N). Rough total:
    for name, mv, nhash in [("MID-64 k=2 n=64", 12.7, 6), ("PROD-256 k=2 n=256", 198.7, 6)]:
        # hash cost: SHAKE128 ~ 1-2us per 168B block; matrix k^2 polys * ~64-512B => few blocks
        hash_us = nhash * (2 if "64" in name and "256" not in name else 8)
        total_us = 6 * mv + hash_us * 4
        print(f"{name}: mat_vec~{mv}us -> full KEM (keygen+encaps+decaps) ~ {total_us:.0f}us portable C")
    print("conclusion: software-only MID-64/PROD-256 KEM in low ms without NTT or assembly.")

if __name__ == "__main__":
    main()

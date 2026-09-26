"""MID-64 keygen timing + P(s)=0 success rate + CPA failure probe."""
import sys
import time
sys.path.insert(0, "ref")
from rmdq_toy import Params, keygen, encrypt, decrypt

def main(trials=20):
    p = Params(n=64, q=3329, k=2, eta=2, w=16, eta_e=2, t=4, m=8)
    ok = 0
    t0 = time.time()
    attempts = []
    for i in range(trials):
        try:
            kg = keygen(p, f"MID-A-{i:04d}".encode().ljust(16, b"0")[:16],
                        f"MID-P-{i:04d}".encode().ljust(16, b"0")[:16],
                        f"MID-S-{i:04d}".encode().ljust(16, b"0")[:16], max_tries=64)
            ok += 1
            attempts.append(kg["attempt"])
        except RuntimeError:
            attempts.append(None)
    dt = time.time() - t0
    print(f"MID-64 keygen: {ok}/{trials} success in {dt:.2f}s ({dt/max(trials,1)*1000:.0f} ms/try)")
    print(f"attempts: {attempts[:10]}")
    # CPA failure probe on first success
    if ok:
        kg = keygen(p, b"MID-A-0000000000", b"MID-P-0000000000", b"MID-S-0000000000", max_tries=64)
        pk = {"A": kg["A"], "b": kg["b"]}
        sk = {"s": kg["s"]}
        fails = 0
        N = 20
        for i in range(N):
            m = bytes([i]) * 32
            ct = encrypt(pk, m, p, f"MID-R-{i:04d}".encode().ljust(16, b"0")[:16])
            bits, _ = decrypt(sk, ct, p)
            obits = []
            for byte in m:
                for b in range(8):
                    obits.append((byte >> b) & 1)
            obits = obits[:p.n]
            if bits[:p.n] != obits[:p.n]:
                fails += 1
        print(f"CPA decrypt fails: {fails}/{N} (toy bound check)")

if __name__ == "__main__":
    main()

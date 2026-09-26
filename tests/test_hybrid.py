import os
import random
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ref"))
from hybrid_attack import guess_trials
from math import comb


def measured_trials(N, wt, eta, g, seed=0, cap=200000):
    """Random (position,value) guesses until g correct hits; compare to model."""
    rnd = random.Random(seed)
    supp = set(rnd.sample(range(N), wt))
    vals = {i: rnd.choice([v for v in range(-eta, eta + 1) if v]) for i in supp}
    if g == 0:
        return 1
    n = 0
    while n < cap:
        n += 1
        gs = rnd.sample(range(N), g)
        gv = [rnd.choice([v for v in range(-eta, eta + 1) if v]) for _ in range(g)]
        # success: EVERY guessed pair is a true (position, value) -- any subset
        if all(gs[i] in vals and gv[i] == vals[gs[i]] for i in range(g)):
            return n
    return None


def test_enumeration_matches_model():
    for N, wt, eta, g in [(16, 4, 1, 1), (16, 4, 1, 2), (32, 6, 1, 1)]:
        pred = guess_trials(N, wt, eta, g)
        got = [measured_trials(N, wt, eta, g, seed=s) for s in range(8)]
        got = [x for x in got if x]
        mean = sum(got) / len(got)
        # geometric-ish: allow 4x band (few samples, heavy tail)
        assert pred / 4 <= mean <= pred * 4, (N, wt, g, pred, mean)
        print(f"N={N} wt={wt} g={g}: predicted {pred:.0f}, measured mean {mean:.0f} "
              f"(samples={got})")


if __name__ == "__main__":
    test_enumeration_matches_model()
    print("HYBRID ENUMERATION OK")

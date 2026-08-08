"""Cosine similarity and its bootstrap confidence interval."""
import numpy as np


def cos(a, b):
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    return float(a @ b / (na * nb)) if na > 0 and nb > 0 else 0.0


def bootstrap_ci(v1, v2, reps, rng):
    """95% bootstrap CI for cos(v1, v2), resampling each vector as a multinomial
    draw from its own citation-count distribution (holding each vector's total
    citation count fixed). Pass a shared rng across repeated calls to
    reproduce a deterministic sequence of draws."""
    t1, t2 = v1.sum(), v2.sum()
    if t1 == 0 or t2 == 0:
        return (np.nan, np.nan)
    p1, p2 = v1 / t1, v2 / t2
    out = np.empty(reps)
    for i in range(reps):
        r1 = rng.multinomial(int(t1), p1).astype(float)
        r2 = rng.multinomial(int(t2), p2).astype(float)
        out[i] = cos(r1, r2)
    return tuple(np.percentile(out, [2.5, 97.5]))

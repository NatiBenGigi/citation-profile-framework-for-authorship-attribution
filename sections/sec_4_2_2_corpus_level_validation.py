#!/usr/bin/env python3
"""
Section 4.2.2 -- Corpus-Level Validation
=========================================
The corpus-wide significance test applied to all 138 authors (N = 9,453
candidate pairs), the enrichment of flagged pairs against the
documented-connection reference set (Table 1), the ten confirmed pairs
(Table 2), and the threshold sensitivity check (Table 3).

Run with:  python sections/sec_4_2_2_corpus_level_validation.py
"""
import os
import sys
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.resources import io
from shared.resources.names import en
from shared.resources.network import build_edges
from shared.resources.display_names import display

COS_THRESHOLD = 0.90     # pairwise flagging threshold
MIN_SHARED = 15          # minimum co-cited-authorities condition

SENS_COS_GRID = (0.85, 0.88, 0.90, 0.92)
SENS_SHARED_GRID = (10, 15, 20)


def hr(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def main():
    A = io.load_corpus()
    bio = io.load_biography()

    X = A.values.astype(float)
    authors = list(A.index)
    N_auth = len(authors)
    Xbool = X > 0
    nrm = np.linalg.norm(X, axis=1)

    set138 = {en(a) for a in authors}
    edges, edges138, typed, _unmatched = build_edges(bio, set138)
    K = len(edges138)

    n_total_pairs = N_auth * (N_auth - 1) // 2
    base = K / n_total_pairs

    # ---- pairwise flagging -------------------------------------------------
    above, share_ok = [], []
    for i, j in combinations(range(N_auth), 2):
        if nrm[i] == 0 or nrm[j] == 0:
            continue
        c = X[i] @ X[j] / (nrm[i] * nrm[j])
        if c > COS_THRESHOLD:
            shared = int((Xbool[i] & Xbool[j]).sum())
            above.append((i, j, c, shared))
            if shared >= MIN_SHARED:
                share_ok.append((i, j, c, shared))

    hr("4.2.2 CORPUS-LEVEL VALIDATION")
    print("N = C(%d, 2) candidate pairs          : %d" % (N_auth, n_total_pairs))
    print("Pairs with cosine similarity > %.2f   : %d" % (COS_THRESHOLD, len(above)))
    print("... imposing >= %d co-cited authorities: m = %d (flagged set)" % (MIN_SHARED, len(share_ok)))

    print("\nIndependent reference set:")
    print("   documented connections K            : %d" % K)
    print("   base rate  pi = K / N               : %d / %d = %.2f%%" % (K, n_total_pairs, base * 100))

    exp_flagged = len(share_ok) * K / n_total_pairs
    print("   expected by chance in m=%d  E[X]     : %.2f" % (len(share_ok), exp_flagged))

    # ---- enrichment: flagged set (m = 52) ----------------------------------
    def hits(pairs):
        return sum(1 for (i, j, _, _) in pairs
                   if frozenset((en(authors[i]), en(authors[j]))) in edges138)

    x_flagged = hits(share_ok)
    m_flagged = len(share_ok)
    prec_flagged = x_flagged / m_flagged
    fold_flagged = prec_flagged / base
    p_flagged = stats.hypergeom.sf(x_flagged - 1, n_total_pairs, K, m_flagged)

    print("\nOf the %d flagged pairs, x = %d are documented connections:" % (m_flagged, x_flagged))
    print("   precision              : %.1f%%" % (prec_flagged * 100))
    print("   fold-enrichment        : %.0f-fold" % fold_flagged)
    print("   one-sided hypergeom. p : %.2e  (p < 0.0001)" % p_flagged)

    print("\nTable 1. Contingency of flagged pairs against documented connections")
    print("                 Connected   Not connected   Total")
    print("   Flagged       %9d   %13d   %5d" % (x_flagged, m_flagged - x_flagged, m_flagged))
    print("   Not flagged   %9d   %13d   %5d" % (K - x_flagged,
                                                   n_total_pairs - K - (m_flagged - x_flagged),
                                                   n_total_pairs - m_flagged))
    print("   Total         %9d   %13d   %5d" % (K, n_total_pairs - K, n_total_pairs))

    # ---- enrichment: unfiltered set (m = 82) -------------------------------
    x_unfilt = hits(above)
    m_unfilt = len(above)
    prec_unfilt = x_unfilt / m_unfilt
    fold_unfilt = prec_unfilt / base
    p_unfilt = stats.hypergeom.sf(x_unfilt - 1, n_total_pairs, K, m_unfilt)

    print("\nUnfiltered candidate set (cosine > %.2f only, no minimum-support filter):" % COS_THRESHOLD)
    print("   flagged pairs           : %d" % m_unfilt)
    print("   documented connections x: %d" % x_unfilt)
    print("   precision               : %.1f%%" % (prec_unfilt * 100))
    print("   fold-enrichment         : %.0f-fold" % fold_unfilt)
    print("   one-sided hypergeom. p  : %.2e  (p < 0.0001)" % p_unfilt)
    print("   => the minimum-support filter removed %d pairs while discarding only %d documented connection(s),"
          % (m_unfilt - m_flagged, x_unfilt - x_flagged))
    print("      raising precision from %.1f%% to %.1f%% and enrichment from %.0f-fold to %.0f-fold."
          % (prec_unfilt * 100, prec_flagged * 100, fold_unfilt, fold_flagged))

    # ---- Table 2: confirmed pairs ------------------------------------------
    hr("Table 2. Flagged pairs confirmed by a documented connection")
    print("%-3s %-42s %-42s %s" % ("#", "Author A", "Author B", "Documented relation"))
    n = 0
    for (i, j, c, sh) in sorted(share_ok, key=lambda t: -t[2]):
        e = frozenset((en(authors[i]), en(authors[j])))
        if e in edges138:
            n += 1
            rel = ", ".join(sorted(typed.get(e, {"connected"})))
            print("%-3d %-42s %-42s %s" % (n, display(authors[i]), display(authors[j]), rel))

    # ---- Table 3: threshold sensitivity (compact) --------------------------
    all_pairs = []
    for i, j in combinations(range(N_auth), 2):
        if nrm[i] == 0 or nrm[j] == 0:
            continue
        c = X[i] @ X[j] / (nrm[i] * nrm[j])
        shared = int((Xbool[i] & Xbool[j]).sum())
        connected = frozenset((en(authors[i]), en(authors[j]))) in edges138
        all_pairs.append((c, shared, connected))

    grid = []
    for ct in SENS_COS_GRID:
        for st in SENS_SHARED_GRID:
            sel = [(c, s, conn) for (c, s, conn) in all_pairs if c > ct and s >= st]
            m = len(sel)
            x = sum(1 for (_, _, conn) in sel if conn)
            prec = x / m if m else np.nan
            fe = (x / m) / base if m else np.nan
            p = stats.hypergeom.sf(x - 1, n_total_pairs, K, m) if m else np.nan
            grid.append({"cosine_gt": ct, "min_shared": st, "m": m, "x": x,
                         "precision_pct": prec * 100, "fold_enrichment": fe, "p": p})
    S = pd.DataFrame(grid)

    loosest = S[(S.cosine_gt == min(SENS_COS_GRID)) & (S.min_shared == min(SENS_SHARED_GRID))]
    chosen = S[(S.cosine_gt == COS_THRESHOLD) & (S.min_shared == MIN_SHARED)]
    weakest = S[S.p == S.p.max()]
    strictest = S[(S.cosine_gt == max(SENS_COS_GRID)) & (S.min_shared == max(SENS_SHARED_GRID))]
    T = pd.concat([loosest, chosen, weakest, strictest]).drop_duplicates().sort_values(["cosine_gt", "min_shared"])

    hr("Table 3. Sensitivity of the corpus-wide significance test to threshold choice")
    print("%-8s %-6s %-6s %-6s %-10s %-13s %-10s %s"
          % ("cosine>", "min_sh", "m", "x", "precision", "fold-enrich.", "p value", "notes"))
    for _, r in T.iterrows():
        note = "Used threshold" if (r.cosine_gt == COS_THRESHOLD and r.min_shared == MIN_SHARED) else ""
        print("%-8.2f %-6d %-6d %-6d %-9.1f%% %-13.0f %-10.1e %s"
              % (r.cosine_gt, r.min_shared, r.m, r.x, r.precision_pct, r.fold_enrichment, r.p, note))

    print("\n" + "=" * 78)
    print("Done -- figures for article Section 4.2.2 only.")
    print("=" * 78)


if __name__ == "__main__":
    main()

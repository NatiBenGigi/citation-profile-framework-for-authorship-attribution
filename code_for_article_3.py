#!/usr/bin/env python3
"""
reproduce_results.py
--------------------
Recomputes every table and statistic reported in the article, directly from the
four source spreadsheets, and prints them to the screen.

Place this file in the SAME FOLDER as the four .xlsx files and run:

    python reproduce_results.py

Required files (same folder):
    authors_vec_profile.xlsx                     138 authors x 220 cited authorities
    similarity_scores.xlsx                       138 x 138 cosine matrix (not strictly needed; recomputed)
    Biography.xlsx                               dates + documented relationships
    chunks_by_daf_p12_and_upper_vec_profile.xlsx  the disputed text's citation profile

Dependencies: pandas, numpy, scipy
"""

import os
import re
import unicodedata
import numpy as np
import pandas as pd
from itertools import combinations
from scipy import stats

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
F_AUTHORS = os.path.join(HERE, "authors_vec_profile.xlsx")
F_BIO     = os.path.join(HERE, "Biography.xlsx")
F_MEYUHAS = os.path.join(HERE, "chunks_by_daf_p12_and_upper_vec_profile.xlsx")


COS_THRESHOLD = 0.90      # pairwise flagging threshold
MIN_SHARED    = 15        # minimum-support condition (co-cited authorities)
SENS_COS_GRID    = (0.85, 0.88, 0.90, 0.92)   # sensitivity grid: cosine thresholds
SENS_SHARED_GRID = (10, 15, 20)               # sensitivity grid: minimum-support values
SENS_CSV         = "sensitivity_grid_results.csv"  # full grid output (set to None to skip)
SENS_TABLE_CSV   = "sensitivity_table_manuscript.csv"  # compact 4-row table for the article (set to None to skip)
BOOT_REPS     = 3000      # bootstrap replicates
BOOT_SEED     = 0         # fixed seed for reproducibility
TPQ_GRACE     = 5         # years of grace on the chronological floor

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 50)


# ----------------------------------------------------------------------------
# Name-normalisation helpers (identical logic to the analysis pipeline)
# ----------------------------------------------------------------------------
def en(s):
    """Normalise an English/transliterated name for matching."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = s.replace("`", "'").replace("\u2019", "'")
    return re.sub(r"\s+", " ", s).strip().lower()


def heb_clean(s):
    """Normalise a Hebrew relationship name: drop leading R' prefix and apostrophes."""
    s = str(s).replace("\xa0", " ")
    s = re.sub(r"^\u05e8['\u05f3`]\s*", "", s.strip())      # drop leading "ר'"
    s = s.replace("'", "").replace("\u05f3", "").replace("`", "")
    return re.sub(r"\s+", " ", s).strip()


def num(x):
    try:
        return float(x)
    except (ValueError, TypeError):
        return np.nan


def cos(a, b):
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    return float(a @ b / (na * nb)) if na > 0 and nb > 0 else 0.0


def hr(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


# ----------------------------------------------------------------------------
# Load data
# ----------------------------------------------------------------------------
def load():
    A = pd.read_excel(F_AUTHORS, index_col=0)
    M = pd.read_excel(F_MEYUHAS, index_col=0)
    # biography: prefer the 'Rshonim only' sheet, else first sheet
    xls = pd.ExcelFile(F_BIO)
    sheet = "Rshonim only" if "Rshonim only" in xls.sheet_names else xls.sheet_names[0]
    bio = pd.read_excel(F_BIO, sheet_name=sheet)
    return A, M, bio


# ----------------------------------------------------------------------------
# Build the documented-connection edge set from the biography
# ----------------------------------------------------------------------------
def build_edges(bio, set138):
    heb2en = {}
    for _, r in bio.iterrows():
        if pd.notna(r["NAME"]) and pd.notna(r["EN_NAME"]):
            heb2en[heb_clean(r["NAME"])] = str(r["EN_NAME"]).replace("\xa0", " ").strip()

    rel_cols = [("Instructor", "teacher-student"),
                ("Teaching Colleague", "teaching colleague"),
                ("Colleague", "colleague")]
    edges = set()
    typed = {}
    unmatched = set()
    for _, r in bio.iterrows():
        if pd.isna(r["EN_NAME"]):
            continue
        src = en(str(r["EN_NAME"]).replace("\xa0", " ").strip())
        for col, lab in rel_cols:
            if col not in bio.columns or pd.isna(r[col]):
                continue
            for t in str(r[col]).split(";"):
                t = heb_clean(t)
                if not t:
                    continue
                if t in heb2en:
                    dst = en(heb2en[t])
                    if dst != src:
                        e = frozenset((src, dst))
                        edges.add(e)
                        typed.setdefault(e, set()).add(lab)
                else:
                    unmatched.add(t)
    edges138 = {e for e in edges if e <= set138}
    return edges, edges138, typed, unmatched


# ----------------------------------------------------------------------------
# Bootstrap confidence interval for a cosine between two count vectors
# ----------------------------------------------------------------------------
def bootstrap_ci(v1, v2, reps=BOOT_REPS, rng=None):
    if rng is None:
        rng = np.random.default_rng(BOOT_SEED)
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


# ============================================================================
# MAIN
# ============================================================================
def main():
    for f in (F_AUTHORS, F_BIO, F_MEYUHAS):
        if not os.path.exists(f):
            raise SystemExit("Missing required file in this folder: %s" % os.path.basename(f))

    A, M, bio = load()
    X = A.values.astype(float)
    authors = list(A.index)
    cols = list(A.columns)
    N_auth = len(authors)
    aidx = {en(a): i for i, a in enumerate(authors)}
    set138 = set(aidx.keys())
    mv = M.iloc[0].values.astype(float)

    # ---- 1. Corpus summary -------------------------------------------------
    hr("1. CORPUS SUMMARY")
    ndist = (X > 0).sum(1)
    print("Citing authors (rows)                : %d" % N_auth)
    print("Cited authorities (columns)          : %d" % len(cols))
    print("Total citations in matrix            : %d" % int(X.sum()))
    print("Distinct authorities cited per author: median=%d  10th pct=%d  min=%d  max=%d"
          % (np.median(ndist), np.percentile(ndist, 10), ndist.min(), ndist.max()))

    # ---- 2. Pairwise flagging pipeline ------------------------------------
    hr("2. PAIRWISE FLAGGING PIPELINE (Section 4.2.2)")
    Xbool = X > 0
    nrm = np.linalg.norm(X, axis=1)
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
    n_total_pairs = N_auth * (N_auth - 1) // 2
    print("Total candidate pairs  N = C(%d,2)   : %d" % (N_auth, n_total_pairs))
    print("Pairs with cosine > %.2f             : %d" % (COS_THRESHOLD, len(above)))
    print("... and sharing >= %d authorities    : %d   (flagged set m)" % (MIN_SHARED, len(share_ok)))

    print("\nMinimum-support cutoff ladder (pairs retained at each threshold):")
    for s in (5, 10, 15, 20, 25, 30):
        cnt = sum(1 for (_, _, _, sh) in above if sh >= s)
        mark = "   <- used" if s == MIN_SHARED else ""
        print("   >= %2d shared authorities : %2d%s" % (s, cnt, mark))

    # ---- 3. Documented-connection network ---------------------------------
    hr("3. DOCUMENTED-CONNECTION REFERENCE NETWORK")
    edges, edges138, typed, unmatched = build_edges(bio, set138)
    K = len(edges138)
    base = K / n_total_pairs
    print("Relationship edges parsed (all)      : %d" % len(edges))
    print("Edges among the 138 corpus authors K : %d" % K)
    print("Base rate  pi = K / N                : %d / %d = %.4f%%" % (K, n_total_pairs, base * 100))
    if unmatched:
        print("\n[warning] %d Hebrew relationship name(s) did not match the bilingual key" % len(unmatched))
        print("          (these do not contribute edges; sample below)")
        for t in list(unmatched)[:8]:
            print("            -", t)

    # ---- 4. Enrichment test (filtered and unfiltered) ---------------------
    hr("4. CORPUS-LEVEL VALIDATION  (enrichment of flagged pairs)")

    def enrich(pairs, label):
        m = len(pairs)
        x = sum(1 for (i, j, _, _) in pairs
                if frozenset((en(authors[i]), en(authors[j]))) in edges138)
        prec = x / m if m else 0.0
        exp = m * K / n_total_pairs
        fe = prec / base if base else float("nan")
        p = stats.hypergeom.sf(x - 1, n_total_pairs, K, m)
        print("%s" % label)
        print("   flagged m              : %d" % m)
        print("   documented hits x      : %d" % x)
        print("   precision  x/m         : %.1f%%" % (prec * 100))
        print("   expected   E[X]=mK/N   : %.2f" % exp)
        print("   fold-enrichment        : %.0fx" % fe)
        print("   one-sided hypergeom. p : %.2e" % p)
        print()
        return m, x

    m1, x1 = enrich(above, "Unfiltered  (cosine > 0.90):")
    m2, x2 = enrich(share_ok, "Flagged set (cosine > 0.90 and >= 15 shared):")

    print("Contingency table for the flagged set (Table 1 in the manuscript):")
    print("                 Connected   Not connected   Total")
    print("   Flagged       %9d   %13d   %5d" % (x2, m2 - x2, m2))
    print("   Not flagged   %9d   %13d   %5d" % (K - x2, n_total_pairs - K - (m2 - x2), n_total_pairs - m2))
    print("   Total         %9d   %13d   %5d" % (K, n_total_pairs - K, n_total_pairs))

    # ---- 4b. Threshold sensitivity analysis --------------------------------
    hr("4b. THRESHOLD SENSITIVITY ANALYSIS  (Appendix)")
    print("Enrichment test rerun across a grid of (cosine threshold x minimum")
    print("shared authorities), to show the result does not depend on the")
    print("specific choice of %.2f / %d.\n" % (COS_THRESHOLD, MIN_SHARED))

    # precompute cosine, shared count, and documented-connection status once
    all_pairs = []
    for i, j in combinations(range(N_auth), 2):
        if nrm[i] == 0 or nrm[j] == 0:
            continue
        c = X[i] @ X[j] / (nrm[i] * nrm[j])
        shared = int((Xbool[i] & Xbool[j]).sum())
        connected = frozenset((en(authors[i]), en(authors[j]))) in edges138
        all_pairs.append((c, shared, connected))

    sens_rows = []
    for ct in SENS_COS_GRID:
        for st in SENS_SHARED_GRID:
            sel = [(c, s, conn) for (c, s, conn) in all_pairs if c > ct and s >= st]
            m = len(sel)
            x = sum(1 for (_, _, conn) in sel if conn)
            prec = x / m if m else np.nan
            exp = m * K / n_total_pairs
            fe = prec / base if (m and base) else np.nan
            p = stats.hypergeom.sf(x - 1, n_total_pairs, K, m) if m else np.nan
            sens_rows.append({"cosine_gt": ct, "min_shared": st, "flagged_m": m,
                              "hits_x": x, "precision_pct": round(prec * 100, 1),
                              "expected_EX": round(exp, 2),
                              "fold_enrichment": round(fe, 0),
                              "hypergeom_p": p})
    S = pd.DataFrame(sens_rows)

    print("   cosine >  shared >=  flagged m  hits x  precision  fold-enr.  hypergeom. p")
    for _, r in S.iterrows():
        mark = "   <- used" if (r.cosine_gt == COS_THRESHOLD and r.min_shared == MIN_SHARED) else ""
        print("   %8.2f  %9d  %9d  %6d  %8.1f%%  %8.0fx  %12.2e%s"
              % (r.cosine_gt, r.min_shared, r.flagged_m, r.hits_x,
                 r.precision_pct, r.fold_enrichment, r.hypergeom_p, mark))

    print("\nRobustness summary: fold-enrichment %.0fx-%.0fx; all p < %.2e"
          % (S.fold_enrichment.min(), S.fold_enrichment.max(), S.hypergeom_p.max() * 1.0001))
    if SENS_CSV:
        out_path = os.path.join(HERE, SENS_CSV)
        S.to_csv(out_path, index=False)
        print("Grid saved to: %s" % out_path)

    # Compact manuscript table: loosest corner, chosen setting, weakest cell,
    # strictest corner (rows selected from the grid, not recomputed).
    if SENS_TABLE_CSV:
        loosest   = S[(S.cosine_gt == min(SENS_COS_GRID)) & (S.min_shared == min(SENS_SHARED_GRID))]
        chosen    = S[(S.cosine_gt == COS_THRESHOLD) & (S.min_shared == MIN_SHARED)]
        weakest   = S[S.hypergeom_p == S.hypergeom_p.max()]
        strictest = S[(S.cosine_gt == max(SENS_COS_GRID)) & (S.min_shared == max(SENS_SHARED_GRID))]
        T = pd.concat([loosest, chosen, weakest, strictest]).drop_duplicates()
        T = T.sort_values(["cosine_gt", "min_shared"]).copy()
        T["note"] = ""
        T.loc[(T.cosine_gt == COS_THRESHOLD) & (T.min_shared == MIN_SHARED), "note"] = "used in main analysis"
        T.loc[T.hypergeom_p == S.hypergeom_p.max(), "note"] = "weakest cell in grid"
        T = T.rename(columns={
            "cosine_gt": "similarity_cutoff", "min_shared": "min_support",
            "flagged_m": "flagged_pairs_m", "hits_x": "documented_connections_x",
            "precision_pct": "precision_pct", "expected_EX": "expected_by_chance",
            "fold_enrichment": "fold_enrichment", "hypergeom_p": "p_value"})
        T["p_value"] = T["p_value"].map(lambda v: "%.1e" % v)
        tbl_path = os.path.join(HERE, SENS_TABLE_CSV)
        T.to_csv(tbl_path, index=False)
        print("Manuscript table (compact, %d rows) saved to: %s" % (len(T), tbl_path))

    # ---- 5. Confirmed pairs (Table 2) -------------------------------------
    hr("5. CONFIRMED FLAGGED PAIRS  (Table 2)")
    print("Flagged pairs that match a documented connection, with relation type:\n")
    n = 0
    for (i, j, c, sh) in sorted(share_ok, key=lambda t: -t[2]):
        e = frozenset((en(authors[i]), en(authors[j])))
        if e in edges138:
            n += 1
            rel = ", ".join(sorted(typed.get(e, {"connected"})))
            print("   %2d. %-34s <-> %-34s [%s]" % (n, authors[i][:34], authors[j][:34], rel))

    # ---- 6. Meyuhas attribution: raw ranking ------------------------------
    hr("6. ATTRIBUTION OF THE DISPUTED TEXT  (raw cosine ranking)")
    m_tot = int(mv.sum())
    m_dist = int((mv > 0).sum())
    print("Disputed text: %d citations across %d distinct authorities\n" % (m_tot, m_dist))
    raw = np.array([cos(X[i], mv) for i in range(N_auth)])
    order = np.argsort(raw)[::-1]

    # death-year map (needed for the chronological filter in section 7, but
    # computed here since the bootstrap CIs below are shared by both sections)
    died = {}
    for _, r in bio.iterrows():
        nm = en(r["EN_NAME"])
        d = num(r["DATE DIED"])
        if np.isnan(d):
            ay = num(r["ADJUSTED YEAR"])
            if not np.isnan(ay):
                d = ay + 25
            else:
                cen = num(r["CENTURY"])
                d = cen * 100 - 50 if not np.isnan(cen) else np.nan
        if not np.isnan(d):
            died[nm] = d

    def dy(name):
        return died.get(en(name), np.nan)

    # terminus post quem = latest-died authority the disputed text cites
    cited_yrs = [(cols[k], dy(cols[k])) for k in range(len(cols))
                 if mv[k] > 0 and not np.isnan(dy(cols[k]))]
    tpq_src, tpq = max(cited_yrs, key=lambda t: t[1])

    # bootstrap 95% CI for the top 20 candidates by raw cosine (shared by
    # sections 6 and 7, so both report the same numbers)
    rng = np.random.default_rng(BOOT_SEED)
    rows = []
    for r in order[:20]:
        v = X[r]
        lo, hi = bootstrap_ci(v, mv, rng=rng)
        width = hi - lo
        d = dy(authors[r])
        reliable = (not np.isnan(width)) and width <= 0.15
        possible = (not np.isnan(d)) and d >= tpq - TPQ_GRACE
        rows.append({
            "author": authors[r], "died": d, "cit": int(v.sum()),
            "sources": int((v > 0).sum()), "shared": int((Xbool[r] & (mv > 0)).sum()),
            "cosine": raw[r], "lo": lo, "hi": hi,
            "reliable": reliable, "admissible": possible,
        })
    R = pd.DataFrame(rows).set_index("author", drop=False)

    print("Top 10 authors by raw cosine similarity to the disputed text:")
    print("   %-36s %8s %8s   %s" % ("author", "cosine", "shared", "95% conf. interval"))
    for r in order[:10]:
        shared = int((Xbool[r] & (mv > 0)).sum())
        a = authors[r]
        if a in R.index:
            ci = "[%.2f, %.2f]" % (R.loc[a, "lo"], R.loc[a, "hi"])
        else:
            ci = "n/a"
        print("   %-36s %8.3f %8d   %s" % (a[:36], raw[r], shared, ci))

    # ---- 7. Reliability + chronology filter (final candidate table) -------
    hr("7. ADMISSIBLE CANDIDATES  (bootstrap 95% CI + chronological filter)")
    print("Latest-died source cited by the disputed text: %s (d. %d)" % (tpq_src, int(tpq)))
    print("=> the author must postdate ~%d; earlier authors are inadmissible.\n" % int(tpq))

    print("Reliable AND chronologically admissible candidates (ranked by cosine):")
    print("   %-34s %5s %7s %7s %6s %7s   %s"
          % ("author", "died", "cit", "sources", "shared", "cosine", "95% conf. interval"))
    for _, r in R[R.reliable & R.admissible].iterrows():
        dd = "?" if np.isnan(r.died) else str(int(r.died))
        print("   %-34s %5s %7d %7d %6d %7.3f   [%.2f, %.2f]"
              % (r.author[:34], dd, r.cit, r.sources, r.shared, r.cosine, r.lo, r.hi))

    print("\nExcluded from the candidate list:")
    for _, r in R[~(R.reliable & R.admissible)].iterrows():
        why = []
        if not r.reliable:
            why.append("unreliable")
        if not r.admissible:
            dd = "?" if np.isnan(r.died) else str(int(r.died))
            why.append("inadmissible (d. %s < %d)" % (dd, int(tpq)))
        print("   %-34s cosine=%.3f  [%.2f, %.2f]  -> %s"
              % (r.author[:34], r.cosine, r.lo, r.hi, "; ".join(why)))

    # ---- 8. Distinctive-source check --------------------------------------
    hr("8. DISTINCTIVE-SOURCE CHECK")
    docf = (X > 0).sum(0)
    disc = sorted([k for k in range(len(cols)) if mv[k] > 0 and docf[k] < 50],
                  key=lambda k: docf[k])
    cand_keys = ["Shem Tov", "Nimmukei", "Yom Tov Asevilli", "Crescas Vidal",
                 "Nissim of Gerona", "Aharon HaLevi", "Shlomo ibn Aderet"]
    cand_labels = ["ShemTov", "NimYosef", "Ritva", "CrescasV", "Ran", "Ra'ah", "Rashba"]
    cand_i, cand_lab = [], []
    for k, lab in zip(cand_keys, cand_labels):
        hit = [i for i, a in enumerate(authors) if k in a]
        if hit:
            cand_i.append(hit[0])
            cand_lab.append(lab)
    print("Discriminating sources the disputed text cites (cited by < 50 of %d authors)." % N_auth)
    print("YES = candidate also cites it.\n")
    header = "df  " + " ".join("%9s" % l for l in cand_lab) + "   source"
    print(header)
    counts = [0] * len(cand_i)
    for k in disc:
        cells = []
        for n_, i in enumerate(cand_i):
            c = Xbool[i, k]
            cells.append("  YES   " if c else "   .    ")
            if c:
                counts[n_] += 1
        print("%2d  %s   %s" % (docf[k], " ".join(cells), str(cols[k]).replace("\xa0", " ")))
    print("\nShared discriminating sources (of %d), by candidate:" % len(disc))
    for lab, c in sorted(zip(cand_lab, counts), key=lambda x: -x[1]):
        print("   %-9s : %d" % (lab, c))

    print("\n" + "=" * 78)
    print("Done. All figures recomputed from the spreadsheets in this folder.")
    print("=" * 78)


if __name__ == "__main__":
    main()
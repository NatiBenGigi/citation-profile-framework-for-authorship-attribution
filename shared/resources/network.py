"""Building the documented-connection reference network from the biography sheet."""
import pandas as pd

from .names import en, heb_clean


def build_edges(bio, set138):
    """Parse teacher/colleague relationships out of the biography sheet.

    Returns (edges, edges138, typed, unmatched):
        edges     -- every parsed relationship, as frozenset({name_a, name_b}) pairs
                      (english-normalised names), regardless of corpus membership
        edges138  -- the subset of edges where both endpoints are among the 138
                      corpus authors (set138)
        typed     -- dict mapping each edge to the set of relationship labels
                      that produced it (teacher-student / teaching colleague / colleague)
        unmatched -- Hebrew relationship names that could not be resolved to an
                      English name via the bilingual key (diagnostic only)
    """
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

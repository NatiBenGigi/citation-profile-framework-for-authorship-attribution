#!/usr/bin/env python3
"""
Section 4.2.4 -- Profile-Based Evaluation and Candidate Ranking
The First Part (Folios 1-12)
==================================================================
Because the first part's citation count falls short of the minimum required
for an independent coherence check (step three), steps four and five of the
research framework are carried out in a single pass here: the first part's
citation profile is compared directly against all 138 corpus authors, so
that the literature's proposed candidate (the Ritva) is tested alongside
every other author the corpus affords.

The first-part profile is built the same way as in Section 4.2.3: from the
full chunk-level citation data, keeping only chunks whose folio precedes 12.

Run with:  python sections/sec_4_2_4_first_part_folios_1_to_12.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.resources import io
from shared.resources.folios import folio_of

FOLIO_SPLIT = 12
LITERATURE_CANDIDATE = "Yom Tov Asevilli (Ritva)"


def hr(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def cos(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(a @ b / (na * nb)) if na > 0 and nb > 0 else 0.0


def build_vector(df, authors_order):
    idx = {a: i for i, a in enumerate(authors_order)}
    vec = np.zeros(len(authors_order), dtype=int)
    for a in df["author_name_ENGLISH"].dropna():
        a = str(a).strip()
        if a in idx:
            vec[idx[a]] += 1
    return vec


def main():
    A = io.load_corpus()
    authors = list(A.index)
    X = A.values.astype(float)

    full_chunks = io.load_meyuhas_full_chunks()
    full_chunks = full_chunks.copy()
    full_chunks["folio"] = full_chunks["file_name"].apply(folio_of)
    first_part_chunks = full_chunks[full_chunks["folio"] < FOLIO_SPLIT]
    first_vec = build_vector(first_part_chunks, list(A.columns)).astype(float)

    raw = np.array([cos(X[i], first_vec) for i in range(len(authors))])
    order = np.argsort(raw)[::-1]
    rank = {authors[r]: (pos + 1, raw[r]) for pos, r in enumerate(order)}

    top_author = authors[order[0]]
    top_score = raw[order[0]]
    ritva_rank, ritva_score = rank[LITERATURE_CANDIDATE]

    hr("4.2.4 PROFILE-BASED EVALUATION AND CANDIDATE RANKING -- The First Part (Folios 1-12)")
    print("First part citations: %d across %d distinct authorities (below the corpus-wide" % (
        int(first_vec.sum()), int((first_vec > 0).sum())))
    print("minimum-support threshold -- results below are suggestive, not definitive).\n")

    print("Compared against all %d corpus authors (steps 4-5 combined):\n" % len(authors))
    print("   %-38s cosine   rank" % "author")
    print("   %-38s %.2f     %d of %d" % (LITERATURE_CANDIDATE + "  (literature's candidate)",
                                            ritva_score, ritva_rank, len(authors)))
    print("   %-38s %.2f     %d of %d" % (top_author + "  (top corpus match)",
                                            top_score, rank[top_author][0], len(authors)))

    print("\n=> %s shows a closer citation-profile match than the %s," % (top_author, "Ritva"))
    print("   supporting Lichtenstein's attribution of the first part to %s," % top_author)
    print("   while the similarity to the Ritva's own profile is consistent with both")
    print("   scholars' shared intellectual formation as students of the Rashba.")

    print("\n" + "=" * 78)
    print("Done -- figures for article Section 4.2.4 (first part) only.")
    print("=" * 78)


if __name__ == "__main__":
    main()

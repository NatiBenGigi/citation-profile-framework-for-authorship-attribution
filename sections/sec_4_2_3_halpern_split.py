#!/usr/bin/env python3
"""
Section 4.2.3 -- Internal Coherence: The Halpern Split
========================================================
Compares the citation profile of the disputed text's first part (folios
preceding folio 12) against its second part (folio 12 to end), following the
division of the commentary proposed by Halpern (1975).

The second part reuses the same citation profile used throughout the rest of
the article's attribution analysis (data/chunks_by_daf_p12_and_upper_vec_profile.xlsx).
The first part is built here from the full chunk-level citation data
(data/chunks_by_daf_with_english.xlsx), keeping only chunks whose folio
(parsed from the Hebrew-numeral file name) precedes 12, with no additional
filtering -- both parts are counted against the same 220-authority space used
by the corpus matrix, exactly as the rest of the pipeline does.

Run with:  python sections/sec_4_2_3_halpern_split.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.resources import io
from shared.resources.folios import folio_of

FOLIO_SPLIT = 12   # first part: folio < FOLIO_SPLIT ; second part: folio >= FOLIO_SPLIT (from Halpern 1975)


def hr(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def cos(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(a @ b / (na * nb)) if na > 0 and nb > 0 else 0.0


def build_vector(df, authors_order):
    """Count citations of each of the 220 corpus authorities within df's rows."""
    idx = {a: i for i, a in enumerate(authors_order)}
    vec = np.zeros(len(authors_order), dtype=int)
    for a in df["author_name_ENGLISH"].dropna():
        a = str(a).strip()
        if a in idx:
            vec[idx[a]] += 1
    return vec


def main():
    full_chunks = io.load_meyuhas_full_chunks()
    second_part_profile = io.load_meyuhas_second_part_profile()
    authors_order = list(second_part_profile.columns)
    second_vec = second_part_profile.iloc[0].values.astype(float)

    full_chunks = full_chunks.copy()
    full_chunks["folio"] = full_chunks["file_name"].apply(folio_of)
    first_part_chunks = full_chunks[full_chunks["folio"] < FOLIO_SPLIT]
    first_vec = build_vector(first_part_chunks, authors_order).astype(float)

    similarity = cos(first_vec, second_vec)

    hr("4.2.3 INTERNAL COHERENCE: THE HALPERN SPLIT")
    print("Division of the commentary at folio %d (Halpern, 1975).\n" % FOLIO_SPLIT)
    print("First part  (folios preceding %d) : %d citations across %d distinct authorities"
          % (FOLIO_SPLIT, int(first_vec.sum()), int((first_vec > 0).sum())))
    print("Second part (folio %d to end)     : %d citations across %d distinct authorities"
          % (FOLIO_SPLIT, int(second_vec.sum()), int((second_vec > 0).sum())))
    print("\nCosine similarity between the two parts' citation profiles: %.2f" % similarity)
    print("=> low similarity: the two parts do not exhibit the citation-profile")
    print("   similarity expected from a unified authorial profile.")

    print("\n" + "=" * 78)
    print("Done -- figures for article Section 4.2.3 only.")
    print("=" * 78)


if __name__ == "__main__":
    main()

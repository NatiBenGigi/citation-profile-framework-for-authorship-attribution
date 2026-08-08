# Article Results Code

Reproducibility code for the results reported in **"You are what you cite: a
citation-profile framework for authorship attribution in citation-rich
traditions"**. This folder is organized **one script per article subsection**
— each script computes and prints exactly the numbers that subsection of the
article reports. It is self-contained (code + data).

### Provenance of `authors_vec_profile.xlsx`

This is the baseline corpus matrix (138 citing authors x 220 cited
authorities, raw citation counts -- see Data dictionary below) and was
produced in three stages, as described in the article:

1. The responsa project corpus was scanned for citations, as described in
   the article.
2. All references to books or rabbis predating 600 CE -- the start of the
   Geonim period (examples: the Bible or the Talmud) were filtered out.
3. Claude AI reviewed the remaining scan results and filtered out incorrect
   references.

Only after these three stages were the surviving references accumulated
into `authors_vec_profile.xlsx`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python article_results_code.py     # runs every section in article order
```

Or run any single section directly, e.g.:

```bash
python sections/sec_4_2_2_corpus_level_validation.py
```

Every script locates `shared/data/` relative to its own file location, so
it can be run from any working directory.

## Repository structure

```
article_results_code.py                         Master script -- runs every section in order.
sections/
    sec_4_2_2_corpus_level_validation.py           Section 4.2.2 -- Corpus-Level Validation
    sec_4_2_3_halpern_split.py                      Section 4.2.3 -- Internal Coherence: The Halpern Split
    sec_4_2_4_first_part_folios_1_to_12.py          Section 4.2.4 -- The First Part (Folios 1-12)
    sec_4_2_4_second_part_folio_12_to_end.py        Section 4.2.4 -- The Second Part (Folio 12 to End)
shared/
    data/                                            The source spreadsheets (see Data dictionary below).
    resources/                                        Code shared by more than one section script.
        io.py                                           Locates and loads the spreadsheets in shared/data/.
        names.py                                        Name-normalisation helpers (Hebrew/English matching).
        network.py                                      Builds the documented teacher/colleague relationship graph.
        similarity.py                                   Cosine similarity + its bootstrap confidence interval.
        folios.py                                       Parses a folio (daf) number from a MEYUHAS chunk file name.
        display_names.py                                Cosmetic, print-only name formatting (never affects computation).
requirements.txt
```

Nothing in `shared/` is section-specific -- it exists only because more than
one section script needs the same loading/matching logic. Each section
script otherwise stands on its own: its `main()` prints only what that part
of the article reports.

## What each section computes

### `sec_4_2_2_corpus_level_validation.py` -- Section 4.2.2, Corpus-Level Validation
The corpus-wide significance test applied to all 138 authors: N = 9,453
candidate pairs, cosine-similarity flagging (82 pairs > 0.90, 52 after the
minimum-support filter), the enrichment test against the K = 81 documented
connections (Table 1), the ten confirmed pairs (Table 2), and the threshold
sensitivity check (Table 3).

### `sec_4_2_3_halpern_split.py` -- Section 4.2.3, Internal Coherence: The Halpern Split
Cosine similarity between the disputed text's first part (folios preceding
12) and second part (folio 12 to end), following the division proposed by
Halpern (1975).

### `sec_4_2_4_first_part_folios_1_to_12.py` -- Section 4.2.4, The First Part (Folios 1-12)
The first part's citation profile compared against all 138 corpus authors
(steps 4-5 of the research framework combined), highlighting the literature's
proposed candidate (the Ritva) against the corpus-wide top match (Crescas
Vidal).

### `sec_4_2_4_second_part_folio_12_to_end.py` -- Section 4.2.4, The Second Part (Folio 12 to End)
Three things: (1) the split-half reliability check -- 1,000 random balanced
partitions of the second part's citation chunks, reporting the distribution
of similarity between the two halves; (2) a direct comparison with the
Ritva's own corpus citation profile; (3) the second part's citation profile
ranked against all 138 corpus authors, with bootstrap 95% confidence
intervals for the top candidates (Table 4).

## Data dictionary (`shared/data/`)

| File | Used by | Contents |
|---|---|---|
| `authors_vec_profile.xlsx` | all sections | 138 x 220 corpus matrix: raw citation counts, one row per citing author, one column per cited authority. |
| `Biography.xlsx` (sheet `Rshonim only`) | 4.2.2 | Author dates and documented relationships (`Instructor`, `Teaching Colleague`, `Colleague` columns). |
| `chunks_by_daf_p12_and_upper_vec_profile.xlsx` | 4.2.3, 4.2.4 (both parts) | The disputed text's second-part (folio 12 to end) citation profile, 1 x 220. |
| `chunks_by_daf_with_english.xlsx` | 4.2.3, 4.2.4 (first part) | Chunk-level citation rows for the entire disputed text (both parts), used to build the first-part (folio < 12) profile. |
| `chunks_by_daf_with_english_p12_and_upper.xlsx` | 4.2.4 (second part) | Chunk-level citation rows for the second part only, used for the split-half reliability check. |

The raw corpus scan behind `authors_vec_profile.xlsx` (see Provenance above)
is too large for git and is published separately as a
[release asset](https://github.com/NatiBenGigi/citation-profile-framework-for-authorship-attribution/releases/download/raw-data_scan-v1/raw.scan.zip).

## Dependencies

pandas, numpy, scipy, openpyxl. See `requirements.txt` for pinned minimum
versions.

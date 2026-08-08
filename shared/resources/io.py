"""Locating and loading the source spreadsheets in data/."""
import os

import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

F_AUTHORS = os.path.join(DATA_DIR, "authors_vec_profile.xlsx")
F_BIO = os.path.join(DATA_DIR, "Biography.xlsx")
F_MEYUHAS_FULL_CHUNKS = os.path.join(DATA_DIR, "chunks_by_daf_with_english.xlsx")
F_MEYUHAS_SECOND_PART = os.path.join(DATA_DIR, "chunks_by_daf_p12_and_upper_vec_profile.xlsx")
F_MEYUHAS_SECOND_PART_CHUNKS = os.path.join(DATA_DIR, "chunks_by_daf_with_english_p12_and_upper.xlsx")


def require(*paths):
    for p in paths:
        if not os.path.exists(p):
            raise SystemExit("Missing required file: %s" % p)


def load_corpus():
    """138 authors x 220 cited authorities, raw citation counts."""
    require(F_AUTHORS)
    return pd.read_excel(F_AUTHORS, index_col=0)


def load_biography():
    """Dates + documented relationships (sheet 'Rshonim only', falling back to the first sheet)."""
    require(F_BIO)
    xls = pd.ExcelFile(F_BIO)
    sheet = "Rshonim only" if "Rshonim only" in xls.sheet_names else xls.sheet_names[0]
    return pd.read_excel(F_BIO, sheet_name=sheet)


def load_meyuhas_full_chunks():
    """Chunk-level (per-source-file) citation rows for the entire disputed text
    (both parts), one row per reference mention, with a 'file_name' column
    encoding the folio (daf)."""
    require(F_MEYUHAS_FULL_CHUNKS)
    return pd.read_excel(F_MEYUHAS_FULL_CHUNKS, sheet_name="Sheet1")


def load_meyuhas_second_part_profile():
    """The disputed text's folio-12-onward citation profile (1 x 220), as used
    throughout the rest of the article's attribution analysis."""
    require(F_MEYUHAS_SECOND_PART)
    return pd.read_excel(F_MEYUHAS_SECOND_PART, index_col=0)


def load_meyuhas_second_part_chunks():
    """Chunk-level (per-source-file) citation rows for the second part only
    (folio 12 to end), used for the split-half reliability check."""
    require(F_MEYUHAS_SECOND_PART_CHUNKS)
    return pd.read_excel(F_MEYUHAS_SECOND_PART_CHUNKS, sheet_name="Sheet1")

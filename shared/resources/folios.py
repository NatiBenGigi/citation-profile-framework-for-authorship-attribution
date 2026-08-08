"""Parsing the folio (daf) number out of a MEYUHAS chunk file name.

Chunk file names follow the pattern "דף_<folio in Hebrew numerals>_<side>_<chunk> .",
e.g. "דף_יב_ב_ב ." is folio יב (12), side ב (b), chunk 2. This module converts the
Hebrew-numeral folio token to an integer via standard gematria letter values.
"""
GEMATRIA = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8, "ט": 9,
    "י": 10, "כ": 20, "ל": 30, "מ": 40, "נ": 50, "ס": 60, "ע": 70, "פ": 80, "צ": 90,
    "ק": 100, "ר": 200, "ש": 300, "ת": 400,
}


def gematria(token):
    return sum(GEMATRIA.get(ch, 0) for ch in str(token))


def folio_of(file_name):
    """Extract the folio number from a chunk file_name, e.g. 'דף_יב_ב_ב .' -> 12."""
    parts = str(file_name).split("_")
    return gematria(parts[1]) if len(parts) >= 2 else None

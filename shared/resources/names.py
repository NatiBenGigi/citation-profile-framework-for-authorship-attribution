"""Name-normalisation helpers used to match author names across spreadsheets."""
import re
import unicodedata

import numpy as np


def en(s):
    """Normalise an English/transliterated name for matching."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = s.replace("`", "'").replace("’", "'")
    return re.sub(r"\s+", " ", s).strip().lower()


def heb_clean(s):
    """Normalise a Hebrew relationship name: drop leading R' prefix and apostrophes."""
    s = str(s).replace("\xa0", " ")
    s = re.sub(r"^ר['׳`]\s*", "", s.strip())      # drop leading "ר'"
    s = s.replace("'", "").replace("׳", "").replace("`", "")
    return re.sub(r"\s+", " ", s).strip()


def num(x):
    """Coerce a spreadsheet cell to float, returning NaN if it isn't numeric."""
    try:
        return float(x)
    except (ValueError, TypeError):
        return np.nan

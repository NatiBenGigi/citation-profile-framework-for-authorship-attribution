"""Cosmetic, print-only name formatting.

This module never touches which author a name refers to -- matching,
matrix indexing, and set membership all use the raw corpus name from
authors_vec_profile.xlsx exactly as-is. `display()` only changes how a name
looks when printed, to match the nickname conventions used in the article's
prose and tables (e.g. adding "(Rashbash)", trimming a redundant
self-referential nickname). If a name isn't listed in OVERRIDES, it is
printed as in the corpus, with only the non-breaking space normalised.
"""

# raw corpus name (after non-breaking-space normalisation) -> article display form
OVERRIDES = {
    "Solomon ben Simon Duran": "Solomon ben Simon Duran (Rashbash)",
    "Meir of Rothenburg (Maharam MeRotenberg)": "Meir of Rothenburg (Maharam)",
    "Mordechai ben Hillel (Mordechai)": "Mordechai ben Hillel",
}


def display(name):
    clean = str(name).replace("\xa0", " ")
    return OVERRIDES.get(clean, clean)

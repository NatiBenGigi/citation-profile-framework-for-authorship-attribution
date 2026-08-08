#!/usr/bin/env python3
"""
article_results_code.py
------------------------
Runs every article-results section script in order, reproducing every figure
reported in the article's results, section by section.

Each section below has a corresponding, standalone script under sections/ of
the same name -- run this file for the full sequence, or run any single
sections/*.py file directly to reproduce just that section. See README.md
for what each section covers.

Run with:  python article_results_code.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sections import sec_4_2_2_corpus_level_validation as sec_4_2_2
from sections import sec_4_2_3_halpern_split as sec_4_2_3
from sections import sec_4_2_4_first_part_folios_1_to_12 as sec_4_2_4_first_part
from sections import sec_4_2_4_second_part_folio_12_to_end as sec_4_2_4_second_part

SECTIONS = [
    sec_4_2_2,
    sec_4_2_3,
    sec_4_2_4_first_part,
    sec_4_2_4_second_part,
]


def main():
    for section in SECTIONS:
        section.main()
        print("\n")


if __name__ == "__main__":
    main()

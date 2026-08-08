"""Shared helpers reused by the per-section scripts in sections/.

Each script under sections/ corresponds to one subsection of the article and
prints only the numbers that subsection reports. This package holds the
plumbing (data loading, name matching) common to more than one of them, so
that logic isn't duplicated across section files.
"""

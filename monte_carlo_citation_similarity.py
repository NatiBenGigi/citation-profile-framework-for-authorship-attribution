import random

import numpy as np
import pandas as pd

#full book
#CHUNKS_FILE = "chunks_by_daf_with_english.xlsx"

#Only from page 12 and upper
CHUNKS_FILE = "chunks_by_daf_with_english_p12_and_upper.xlsx"
OUTPUT_FILE = "citation_split_similarity_results.xlsx"
N_ITERATIONS = 1000
RANDOM_SEED = 42


def is_empty(value):
    return pd.isna(value) or str(value).strip() == ""


def build_groups(df, authors):
    author_index = {author: i for i, author in enumerate(authors)}
    n_authors = len(authors)

    groups = []
    for file_name, group_df in df.groupby("file_name"):
        vector = np.zeros(n_authors, dtype=int)
        for author in group_df["author_name_ENGLISH"]:
            if not is_empty(author):
                vector[author_index[author]] += 1

        groups.append({
            "file_name": file_name,
            "total_rows": len(group_df),
            "vector": vector,
        })

    return groups


def greedy_balanced_split(groups, rng):
    order = list(range(len(groups)))
    rng.shuffle(order)

    rows_a, rows_b = 0, 0
    vec_a = np.zeros_like(groups[0]["vector"])
    vec_b = np.zeros_like(groups[0]["vector"])
    groups_a, groups_b = 0, 0

    for i in order:
        g = groups[i]
        if rows_a <= rows_b:
            rows_a += g["total_rows"]
            vec_a += g["vector"]
            groups_a += 1
        else:
            rows_b += g["total_rows"]
            vec_b += g["vector"]
            groups_b += 1

    return vec_a, vec_b, rows_a, rows_b, groups_a, groups_b


def cosine_similarity(a, b):
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return np.nan
    return float(np.dot(a, b) / (norm_a * norm_b))


def main():
    df = pd.read_excel(CHUNKS_FILE, sheet_name="Sheet1")

    authors = sorted(df["author_name_ENGLISH"].dropna().unique().tolist())
    groups = build_groups(df, authors)

    print(f"Total rows: {len(df)}")
    print(f"Total groups (file_name): {len(groups)}")
    print(f"Unique resolved authors: {len(authors)}")

    rng = random.Random(RANDOM_SEED)
    results = []

    for iteration in range(1, N_ITERATIONS + 1):
        vec_a, vec_b, rows_a, rows_b, groups_a, groups_b = greedy_balanced_split(groups, rng)
        similarity = cosine_similarity(vec_a, vec_b)

        results.append({
            "iteration": iteration,
            "groups_A": groups_a,
            "groups_B": groups_b,
            "rows_A": rows_a,
            "rows_B": rows_b,
            "resolved_citations_A": int(vec_a.sum()),
            "resolved_citations_B": int(vec_b.sum()),
            "cosine_similarity": similarity,
        })

    results_df = pd.DataFrame(results)
    results_df.to_excel(OUTPUT_FILE, sheet_name="iterations", index=False)

    sims = results_df["cosine_similarity"].dropna()
    print("\nCosine similarity across iterations:")
    print(f"  mean:   {sims.mean():.4f}")
    print(f"  std:    {sims.std():.4f}")
    print(f"  min:    {sims.min():.4f}")
    print(f"  max:    {sims.max():.4f}")
    print(f"  median: {sims.median():.4f}")
    print(f"  range:  {sims.min():.4f} - {sims.max():.4f}")
    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

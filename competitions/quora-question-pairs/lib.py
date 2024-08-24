import pandas as pd
import re
from string import punctuation
from os import path


def clean_data(file_path, debug=False, save_path=None):
    # Load the dataset
    df = pd.read_csv(file_path)
    print("Field Names:", ", ".join(df.columns.tolist()))
    print("Number of Rows:", len(df))

    # Handling Missing Values
    original_df = df.copy()
    df.dropna(subset=["question1", "question2"], inplace=True)

    if debug:
        dropped_rows = original_df[~original_df.index.isin(df.index)]
        print("Generate dropped rows")
        dropped_rows.to_csv(path.join(save_path, "missing_values.csv"), index=True)

    # Text Normalization
    def normalize_text(text):
        text = text.lower()  # Lowercase
        text = re.sub(f"[{punctuation}]", "", text)  # Remove punctuation
        text = re.sub(r"\s+", " ", text).strip()  # Remove extra whitespace
        return text

    original_questions = df[["question1", "question2"]].copy()
    df["question1"] = df["question1"].apply(normalize_text)
    df["question2"] = df["question2"].apply(normalize_text)

    if debug:
        normalized_questions = df[["question1", "question2"]]
        comparison_df = pd.concat([original_questions, normalized_questions], axis=1)
        comparison_df.columns = [
            "original_question1",
            "original_question2",
            "normalized_question1",
            "normalized_question2",
        ]
        print("Generate text normalization comparisons")
        comparison_df.to_csv(path.join(save_path, "text_norm_cmp.csv"), index=True)

    # Removing Duplicate Rows
    original_df = df.copy()
    df.drop_duplicates(subset=["qid1", "qid2"], inplace=True)

    if debug:
        duplicate_rows = original_df[~original_df.index.isin(df.index)]
        print("Generate duplicate rows")
        duplicate_rows.to_csv(path.join(save_path, "duplicate_rows.csv"), index=True)

    # Handling Outliers
    def is_outlier(text):
        return len(text.split()) < 2 or len(text.split()) > 100

    original_df = df.copy()
    df = df[~df["question1"].apply(is_outlier)]
    df = df[~df["question2"].apply(is_outlier)]
    if debug:
        outlier_rows = original_df[~original_df.index.isin(df.index)]
        print("Generate outlier rows")
        outlier_rows.to_csv(path.join(save_path, "outlier_rows.csv"), index=True)

    df.to_csv(path.join(save_path, "cleaned_train.csv"), index=True)

import re
import pandas as pd

def text_to_table(text):
    """
    Convert OCR text into structured DataFrame.
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return pd.DataFrame()
    split_lines = [re.split(r'\s{2,}|\t', line) for line in lines]
    max_cols = max(len(row) for row in split_lines)
    for row in split_lines:
        while len(row) < max_cols:
            row.append("")
    df = pd.DataFrame(split_lines)
    if df.shape[0] > 1:
        df.columns = df.iloc[0]
        df = df.drop(0).reset_index(drop=True)
    return df


import pandas as pd
import sys

file_path = r"c:\Users\ninni\Documents\projects\freee\money_forward\freee_import_2025.xlsx"
try:
    df = pd.read_excel(file_path, nrows=5)
    print("Columns:", df.columns.tolist())
    print("Sample Data:")
    print(df.to_string())
except Exception as e:
    print(e)

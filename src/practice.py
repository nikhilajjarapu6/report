import pdfplumber
import pandas as pd
import tabula

# def extract_from_tables(pdf_path):
#     tables=[]
#     with pdfplumber.open(pdf_path) as pdf:
#         for page in pdf.pages:
#             table = page.extract_table()
#             tables.append(table)

#     df = pd.DataFrame(tables)
#     return df

# df_tables = extract_from_tables(r"D:\Nikhil\python\report_analysis\data\raw\KIMS _ EHR (19).pdf")
# print(df_tables.head())
# df_tables.to_csv("tests_tables.csv", index=False)

pdf_path = r"D:\Nikhil\python\blood_report\files\KIMS _ EHR (19).pdf"

tables = tabula.read_pdf(pdf_path, pages='1-15', multiple_tables=True)

print(f"Total tables found: {len(tables)}")

for i, t in enumerate(tables):
    print(f"\n--- Table {i+1} ---")
    print(t.head(8))

import sqlite3
print(sqlite3.sqlite_version)

# import tabula
# import pandas as pd

# def extract_tables_from_pdf(pdf_path):
#     # 读取PDF文件中的所有表格
#     tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
#     return tables

# pdf_path = 'downloads/000050_深天马Ａ/20220622_深天马Ａ：《公司章程》修订对照表.pdf'
# tables = extract_tables_from_pdf(pdf_path)

# # 遍历每个表格
# for i, table in enumerate(tables, start=1):
#     print(f"Table {i}:")
#     # 遍历表格的每一行
#     for index, row in table.iterrows():
#         import pdb
#         pdb.set_trace()
#         print(row)

import camelot

def extract_tables_from_pdf(pdf_path):
    # 读取PDF文件中的所有表格
    tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream')
    return tables

pdf_path = 'downloads/000050_深天马Ａ/20220622_深天马Ａ：《公司章程》修订对照表.pdf'
tables = extract_tables_from_pdf(pdf_path)
for table in tables:
    print(table.df)
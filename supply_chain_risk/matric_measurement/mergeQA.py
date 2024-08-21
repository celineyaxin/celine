import jieba
import pandas as pd
import os
import re
from tqdm import tqdm

def load_unique_words(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        words = {line.strip() for line in file}
    return words

def remove_salutations(text):
    if pd.isna(text):  # 检查是否为 NaN 值
        return ''
    pattern = re.compile(r'请问[\u4e00-\u9fa5\s]+?(?=[，、：])')
    filtered_text = pattern.sub('', text)
    return filtered_text

def remove_specific_greetings(text):
    if pd.isna(text):  # 检查是否为 NaN 值
        return ''
    # greetings_pattern = re.compile(r'[\u4e00-\u9fa5]+(?:\s+[\u4e00-\u9fa5]+)*[，、]\s*[你您]+\s*[好]')
    greetings_pattern = re.compile(r'[\u4e00-\u9fa5]+(?:[你您]+)?\s*(?:好|您好|你好)\s*[，、！]')
    filtered_text = greetings_pattern.sub('', text)
    return filtered_text

def merge_excel_files(folder_path, file1, file2,columns_to_keep):
    file1_path = os.path.join(folder_path, file1)
    df1 = pd.read_excel(file1_path)
    file2_path = os.path.join(folder_path, file2)
    df2 = pd.read_excel(file2_path)
    df1['Year'] = pd.to_numeric(df1['Year'], errors='coerce')
    df2['Year'] = pd.to_numeric(df2['Year'], errors='coerce')
    df1 = df1[(df1['Year'] >= 2010) & (df1['Year'] <= 2023)]
    df2 = df2[(df2['Year'] >= 2010) & (df2['Year'] <= 2023)]
    merged_df = pd.concat([df1, df2], ignore_index=True)
    merged_df = merged_df[columns_to_keep]
    merged_df['Qcntet'] = merged_df['Qcntet'].apply(lambda x: str(x) if not pd.isna(x) else '') 
    merged_df['Qcntet'] = merged_df['Qcntet'].apply(remove_salutations)
    merged_df['Qcntet'] = merged_df['Qcntet'].apply(remove_specific_greetings)
    merged_df['合并后的问答内容'] = merged_df['Qcntet'] + ' ' + merged_df['Acntet']
    df_filtered = merged_df[['Scode', 'Year', '合并后的问答内容']]
    return df_filtered

def group_and_merge_texts(merged_df, group_columns, text_column, output_column_name):
    merged_df['Scode'] = merged_df['Scode'].astype(str).str.strip()
    merged_df['Year'] = merged_df['Year'].astype(str).str.strip()
    merged_df[text_column] = merged_df[text_column].dropna()
    merged_df.dropna(subset=group_columns, inplace=True)
    grouped = merged_df.groupby(group_columns)
    merged_df = grouped[text_column].agg(lambda x: ' '.join(x.astype(str))).reset_index()
    merged_df.rename(columns={text_column: output_column_name}, inplace=True)
    merged_df.reset_index(drop=True, inplace=True)
    merged_df.drop_duplicates(subset=group_columns, inplace=True)   
    return merged_df
    
folder_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/原始数据/业绩说明会问答文本分析' 
# folder_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/test'  
file1 = '业绩说明会问答文本分析_1.xlsx'  
file2 = '业绩说明会问答文本分析_2.xlsx'  
columns_to_keep = ['Scode', 'Year', 'Qcntet','Acntet']
df_filtered=merge_excel_files(folder_path, file1, file2,columns_to_keep)

grouped_df = group_and_merge_texts(
    merged_df=df_filtered,
    group_columns=['Scode', 'Year'],
    text_column='合并后的问答内容',  # 使用新创建的列名
    output_column_name='Content'
)
output_file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/groupqa.csv'
grouped_df.to_csv(output_file_path, index=False)

# output_file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/groupqa.csv'
# df_filtered.to_csv(output_file_path, index=False)

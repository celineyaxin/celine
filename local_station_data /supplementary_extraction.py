import pandas as pd
import os
from random import sample
from multiprocessing import Pool
from tqdm import tqdm 
import chardet

# 定义关键词列表
keyFilterWord = ['借钱', '贷款', '还款', '催收', '借款', '利息', '利率', '砍头息']

# 检查投诉内容是否包含关键词
def contains_keywords(complaint_content, keywords):
    if isinstance(complaint_content, str): 
        return any(keyword in complaint_content for keyword in keywords)
    return False  

def load_complaint_sellers(excel_path):
    df = pd.read_excel(excel_path, sheet_name='Sheet1')
    return df['投诉商家'].tolist()

def detect_encoding(file):
    with open(file, 'rb') as f:
        result = chardet.detect(f.read())  # 检测文件编码
    return result['encoding']

def process_single_csv(file, sellers, keywords):
    encoding = detect_encoding(file)
    df = pd.read_csv(file, encoding=encoding)
    df['发起投诉内容'] = df['发起投诉内容'].fillna('')  
    df = df.dropna(subset=['发起投诉内容']) 
    if '投诉对象' in df.columns:
        filtered_df = df[df['投诉对象'].isin(sellers)][['投诉对象', '投诉编号', '发起投诉内容']]
        if not filtered_df.empty:
            grouped = filtered_df.groupby('投诉对象')
            complaints = []
            for name, group in grouped:
                if len(group) > 10:
                    sampled_indices = sample(group.index.tolist(), 10)
                    sampled_group = group.loc[sampled_indices]
                else:
                    sampled_group = group
                keyword_count = sampled_group['发起投诉内容'].apply(contains_keywords, args=(keywords,)).sum()
                if keyword_count >= 2:
                # if sampled_group['发起投诉内容'].apply(contains_keywords, args=(keywords,)).any():  #只要有一条
                    for _, complaint in sampled_group.iterrows():
                        complaints.append({
                            '投诉对象': name,
                            '投诉编号': complaint['投诉编号'],
                            '投诉内容': complaint['发起投诉内容']
                        })
            return pd.DataFrame(complaints)
    else:
        print(f"'投诉对象' column not found in {file}")
        return pd.DataFrame() 

def process_csv_files(folder_path, sellers, keywords):
    csv_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.csv') and not f.startswith('.')]
    args_list = [(file, sellers, keywords) for file in csv_files]
    pool = Pool()
    results = pool.starmap(process_single_csv, tqdm(args_list, desc="Processing CSV files"))
    pool.close()
    pool.join()
    all_complaints = pd.concat(results, ignore_index=True)
    return all_complaints

if __name__ == '__main__':
    excel_path = '/Users/chenyaxin/Desktop/地方站导出数据/原始数据处理/待提取商家列表.xlsx'
    folder_path = '/Volumes/yaxindedisk 1/黑猫原始网页数据备份/merge_data2'
    # folder_path = '/Users/chenyaxin/Desktop/地方站导出数据/原始数据处理/test'
    sellers = load_complaint_sellers(excel_path)
    filtered_df = process_csv_files(folder_path, sellers,keyFilterWord)

# 打印或保存提取的数据
    print(filtered_df)
    # 如果需要保存到文件
    filtered_df.to_csv('/Users/chenyaxin/Desktop/地方站导出数据/原始数据处理/to_be_extracted_complaints.csv', index=False)
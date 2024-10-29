# 根据生成的20个文件计算相似度
import pandas as pd
from multiprocessing import Pool
from fuzzywuzzy import fuzz
from tqdm.auto import tqdm
import os
def process_complaints(file_path, threshold, encoding_list, min_length_diff):
    new_rows = []
    df = pd.read_csv(file_path)
    for encoding in encoding_list:
        # print(encoding)
        df_subset = df[df['编码'] == encoding]  # 只获取当前编码的子集
        # print(df_subset)
        if '投诉内容' in df_subset.columns:
            df_complaints = df_subset[['投诉内容', '投诉编号']].dropna().values.tolist()
            # print(df_complaints)
            for i in tqdm(range(len(df_complaints))):
                content1 = df_complaints[i][0]
                for j in range(i + 1, len(df_complaints)):
                    content2 = df_complaints[j][0]
                    length_diff = abs(len(content1) - len(content2))
                    if length_diff <= min_length_diff:
                        similarity = fuzz.ratio(df_complaints[i], df_complaints[j])
                        if similarity > threshold:
                            new_row = {
                                '编码': encoding_list[0],  # 取编码列表的第一个值作为代表
                                '相似度': similarity,
                                '投诉内容1': df_complaints[i][0],  # 投诉内容
                                '投诉编号1': df_complaints[i][1],  # 投诉编号
                                '投诉内容2': df_complaints[j][0],
                                '投诉编号2': df_complaints[j][1]
                            }
                            new_rows.append(new_row)
        
    return pd.DataFrame(new_rows)


def merge_results(results):
    non_empty_results = [r for r in results if isinstance(r, pd.DataFrame) and not r.empty]
    merged_df = pd.concat(non_empty_results, ignore_index=True)
    return merged_df 
 
if __name__ == '__main__':
    file_path = '/Users/chenyaxin/Desktop/websitdata/similarity/updated_complaints_part_3.csv'  # 替换为实际文件路径
    threshold = 80  # 设置相似度阈值
    min_length_diff = 20
    num_processes = 4  # 根据你的CPU核心数设置进程数
    df = pd.read_csv(file_path)
    df['编码'] = df['编码'].astype(int)
    unique_encodings = sorted(df['编码'].dropna().unique())
    chunk_size = (len(unique_encodings) + num_processes - 1) // num_processes
    encoding_lists = [unique_encodings[i:i + chunk_size] for i in range(0, len(unique_encodings), chunk_size)]

    with Pool(processes=num_processes) as pool:
        args_list = [(file_path, threshold, encoding_list, min_length_diff) for encoding_list in encoding_lists]
        results = list(tqdm(pool.starmap(process_complaints, args_list), total=len(args_list)))
    duplicates_df = merge_results(results)

# # 输出结果到CSV文件
    output_path = './similar_complaints_3.csv'  
    duplicates_df.to_csv(output_path, index=False)
    print(f"相似投诉内容及相似度筛选完成，结果已保存到 '{output_path}'")
    
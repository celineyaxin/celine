import pandas as pd
import os
import glob
import gc
import time

def load_complaint_ids(complaint_ids_file):
    """只加载投诉编号，不创建复杂的数据结构"""
    print("加载投诉编号...")
    
    if complaint_ids_file.endswith('.csv'):
        complaint_df = pd.read_csv(complaint_ids_file)
        complaint_ids = set(complaint_df['投诉编号'].astype(str).unique())
        # 保存原始顺序和可能的其他列
        original_order = complaint_df['投诉编号'].astype(str).tolist()
        original_df = complaint_df
    else:
        with open(complaint_ids_file, 'r', encoding='utf-8') as f:
            complaint_ids = [line.strip() for line in f if line.strip()]
        original_order = complaint_ids.copy()
        complaint_ids = set(complaint_ids)
        original_df = pd.DataFrame(complaint_ids, columns=['投诉编号'])
    
    print(f"加载了 {len(complaint_ids)} 个投诉编号")
    return complaint_ids, original_order, original_df

def extract_features_from_files(csv_folder, target_complaint_ids):
    """
    从所有CSV文件中提取目标投诉编号的特征
    返回一个字典：{投诉编号: [商家回复时间1, 发起投诉时间]}
    """
    csv_files = glob.glob(os.path.join(csv_folder, "*.csv"))
    print(f"找到 {len(csv_files)} 个CSV文件")
    
    # 初始化特征字典
    features_dict = {}
    
    # 跟踪尚未找到的投诉编号
    remaining_ids = target_complaint_ids.copy()
    
    for i, file_path in enumerate(csv_files, 1):
        if not remaining_ids:
            break
            
        print(f"处理文件 {i}/{len(csv_files)}: {os.path.basename(file_path)}")
        file_start = time.time()
        
        try:
            # 分块读取文件，只保留两个时间列
            chunk_iter = pd.read_csv(
                file_path, 
                usecols=['投诉编号', '商家回复时间1', '发起投诉时间'],
                chunksize=50000,
                dtype={'投诉编号': str}
            )
            
            file_matched = 0
            for chunk_num, chunk in enumerate(chunk_iter):
                # 过滤出我们需要的投诉编号
                mask = chunk['投诉编号'].isin(remaining_ids)
                matched_chunk = chunk[mask]
                
                if not matched_chunk.empty:
                    # 更新特征字典
                    for _, row in matched_chunk.iterrows():
                        complaint_id = row['投诉编号']
                        if complaint_id not in features_dict:
                            features_dict[complaint_id] = [
                                row['商家回复时间1'],
                                row['发起投诉时间']
                            ]
                            file_matched += 1
                    
                    # 更新剩余未匹配的编号
                    remaining_ids = remaining_ids - set(features_dict.keys())
                    
                    if not remaining_ids:
                        break
                
                # 每处理10个块输出一次进度
                if chunk_num % 10 == 0:
                    print(f"  已处理 {chunk_num} 个数据块，剩余未匹配: {len(remaining_ids)}")
                
                # 清理内存
                del chunk, matched_chunk
                gc.collect()
            
            file_time = time.time() - file_start
            print(f"  本文件匹配: {file_matched} 条记录, 耗时: {file_time:.2f}秒")
            print(f"  总匹配进度: {len(features_dict)}/{len(target_complaint_ids)} ({len(features_dict)/len(target_complaint_ids)*100:.2f}%)")
            
        except Exception as e:
            print(f"处理文件 {os.path.basename(file_path)} 时出错: {e}")
            continue
    
    return features_dict

def merge_features_to_original(original_df, features_dict, original_order):
    """将提取的特征合并到原始数据中"""
    print("将特征合并到原始数据中...")
    
    # 创建特征DataFrame
    features_data = []
    for complaint_id in original_order:
        if complaint_id in features_dict:
            features = features_dict[complaint_id]
            features_data.append({
                '商家回复时间1': features[0],
                '发起投诉时间': features[1]
            })
        else:
            features_data.append({
                '商家回复时间1': None,
                '发起投诉时间': None
            })
    
    features_df = pd.DataFrame(features_data)
    
    # 如果原始数据有其他列，需要合并
    if '投诉编号' in original_df.columns and len(original_df.columns) > 1:
        # 合并原始数据和特征数据
        result_df = original_df.copy()
        result_df['商家回复时间1'] = features_df['商家回复时间1']
        result_df['发起投诉时间'] = features_df['发起投诉时间']
    else:
        # 如果原始数据只有投诉编号，直接创建新DataFrame
        result_df = pd.DataFrame({
            '投诉编号': original_order,
            '商家回复时间1': features_df['商家回复时间1'],
            '发起投诉时间': features_df['发起投诉时间']
        })
    
    return result_df

def efficient_data_processing(csv_folder, complaint_ids_file, output_file):
    """
    高效数据处理主函数
    """
    print("开始高效数据处理...")
    start_time = time.time()
    
    # 步骤1: 加载投诉编号
    complaint_ids, original_order, original_df = load_complaint_ids(complaint_ids_file)
    
    # 步骤2: 从CSV文件中提取特征
    features_dict = extract_features_from_files(csv_folder, complaint_ids)
    
    # 步骤3: 将特征合并到原始数据中
    result_df = merge_features_to_original(original_df, features_dict, original_order)
    
    # 步骤4: 保存结果
    print(f"保存结果到 {output_file}...")
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    # 输出统计信息
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n处理完成!")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"成功匹配: {len(features_dict)}/{len(complaint_ids)} 条记录 ({len(features_dict)/len(complaint_ids)*100:.2f}%)")
    
    # 输出各列的匹配情况
    for col in ['商家回复时间1', '发起投诉时间']:
        matched_count = result_df[col].notna().sum()
        print(f"  {col}: {matched_count}/{len(result_df)} ({matched_count/len(result_df)*100:.2f}%)")

if __name__ == "__main__":
    csv_folder = "/Volumes/T9/merge_data2"
    complaint_ids_file = "/Users/chenyaxin/Desktop/websitdata/merge_data6/delete_hostility.csv"
    output_file = "/Users/chenyaxin/Desktop/privacy/data/complaints_feature.csv"
    
    efficient_data_processing(csv_folder, complaint_ids_file, output_file)
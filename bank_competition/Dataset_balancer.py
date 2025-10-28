import pandas as pd
import numpy as np
from collections import Counter
import random
from datetime import datetime

def balance_dataset_with_distribution(file_path, output_path):
    """
    平衡数据集，同时考虑商家和年份分布
    
    参数:
    file_path: 输入Excel文件路径
    output_path: 输出Excel文件路径
    """
    
    # 读取数据
    df = pd.read_excel(file_path)
    print(f"原始数据总条数: {len(df)}")
    
    # 删除分类错误的样本
    df = df[df['分类结果_qwen'] != '分类错误']
    print(f"删除分类错误后数据条数: {len(df)}")
    
    # 从发布时间提取年份
    df = extract_year_from_publish_time(df)
    
    # 目标数量配置
    target_counts = {
        '催收行为类': 1000,
        '定价收费类': 1000,
        '客户服务类': 1000,
        '营销宣传类': 1000,
        '其他类': None,  # None表示保持原数量
        '合同条款类': None
    }
    
    balanced_dfs = []
    
    for category, target_count in target_counts.items():
        # 获取该类别的数据
        category_df = df[df['分类结果_qwen'] == category].copy()
        current_count = len(category_df)
        
        print(f"\n处理类别: {category}")
        print(f"当前数量: {current_count}")
        
        if target_count is None:
            # 保持原数量
            balanced_df = category_df
            print(f"保持原数量: {current_count}")
        elif current_count > target_count:
            # 需要下采样
            balanced_df = stratified_downsample(category_df, target_count)
            print(f"下采样到: {len(balanced_df)}")
        else:
            # 数量不足，保持原样
            balanced_df = category_df
            print(f"数量不足，保持原样: {current_count}")
        
        # 显示采样后的分布情况
        if len(balanced_df) > 0:
            merchant_dist = balanced_df['compn'].value_counts()
            year_dist = balanced_df['年份'].value_counts()
            print(f"商家分布: {dict(merchant_dist.head())}...")
            print(f"年份分布: {dict(year_dist)}")
        
        balanced_dfs.append(balanced_df)
    
    # 合并所有类别
    final_df = pd.concat(balanced_dfs, ignore_index=True)
    
    # 统计最终分布
    final_distribution = final_df['分类结果_qwen'].value_counts()
    print(f"\n最终数据分布:")
    for category, count in final_distribution.items():
        percentage = count / len(final_df) * 100
        print(f"{category}: {count} 条 ({percentage:.1f}%)")
    
    # 保存结果
    final_df.to_excel(output_path, index=False)
    print(f"\n结果已保存到: {output_path}")
    print(f"总样本数: {len(final_df)}")
    
    return final_df

def extract_year_from_publish_time(df):
    """
    从发布时间列提取年份信息
    
    参数:
    df: 包含发布时间列的DataFrame
    
    返回:
    添加了年份列的DataFrame
    """
    # 假设发布时间列名为'发布时间'，格式为'2021-12-10 12:29:00'
    if '发布时间' not in df.columns:
        print("警告: 数据中未找到'发布时间'列")
        # 创建一个默认的年份列，全部设为当前年份
        df['年份'] = datetime.now().year
        return df
    
    # 提取年份
    def extract_year(time_str):
        try:
            # 处理不同的时间格式
            if pd.isna(time_str):
                return None
            if isinstance(time_str, str):
                # 尝试解析日期时间字符串
                if ' ' in time_str:
                    date_part = time_str.split(' ')[0]
                else:
                    date_part = time_str
                
                # 提取年份
                if '-' in date_part:
                    year = int(date_part.split('-')[0])
                elif '/' in date_part:
                    year = int(date_part.split('/')[0])
                else:
                    # 如果无法解析，返回None
                    return None
                
                # 确保年份在合理范围内
                if 2000 <= year <= 2030:
                    return year
                else:
                    return None
            elif isinstance(time_str, (pd.Timestamp, datetime)):
                return time_str.year
            else:
                return None
        except:
            return None
    
    df['年份'] = df['发布时间'].apply(extract_year)
    
    # 统计年份分布
    year_counts = df['年份'].value_counts().sort_index()
    print("年份分布:")
    for year, count in year_counts.items():
        print(f"  {year}: {count}条")
    
    # 如果有无法提取年份的数据，使用众数填充
    if df['年份'].isna().any():
        mode_year = df['年份'].mode()[0] if not df['年份'].mode().empty else datetime.now().year
        df['年份'] = df['年份'].fillna(mode_year)
        print(f"使用众数 {mode_year} 填充了 {df['年份'].isna().sum()} 条缺失年份数据")
    
    return df

def stratified_downsample(df, target_count):
    """
    分层下采样，尽量保持商家和年份分布均衡
    
    参数:
    df: 要下采样的DataFrame
    target_count: 目标数量
    
    返回:
    下采样后的DataFrame
    """
    
    # 计算当前分布
    merchant_counts = df['compn'].value_counts()
    year_counts = df['年份'].value_counts()
    
    # 计算每个商家应该保留的大致数量比例
    merchant_ratios = merchant_counts / len(df)
    target_merchant_counts = (merchant_ratios * target_count).round().astype(int)
    
    # 调整目标数量，确保总和等于target_count
    total = target_merchant_counts.sum()
    if total != target_count:
        diff = target_count - total
        # 在数量最多的商家中调整
        largest_merchant = target_merchant_counts.idxmax()
        target_merchant_counts[largest_merchant] += diff
    
    sampled_dfs = []
    
    for merchant, merchant_target in target_merchant_counts.items():
        merchant_df = df[df['compn'] == merchant]
        current_merchant_count = len(merchant_df)
        
        if current_merchant_count <= merchant_target:
            # 如果当前数量小于等于目标，全部保留
            sampled_merchant = merchant_df
        else:
            # 在商家内部按年份分层采样
            year_counts_in_merchant = merchant_df['年份'].value_counts()
            year_ratios = year_counts_in_merchant / current_merchant_count
            target_year_counts = (year_ratios * merchant_target).round().astype(int)
            
            # 调整年份目标数量
            year_total = target_year_counts.sum()
            if year_total != merchant_target:
                diff = merchant_target - year_total
                largest_year = target_year_counts.idxmax()
                target_year_counts[largest_year] += diff
            
            year_samples = []
            for year, year_target in target_year_counts.items():
                year_df = merchant_df[merchant_df['年份'] == year]
                if len(year_df) <= year_target:
                    year_sample = year_df
                else:
                    year_sample = year_df.sample(n=year_target, random_state=42)
                year_samples.append(year_sample)
            
            sampled_merchant = pd.concat(year_samples, ignore_index=True)
        
        sampled_dfs.append(sampled_merchant)
    
    # 合并所有采样结果
    result_df = pd.concat(sampled_dfs, ignore_index=True)
    
    # 如果由于四舍五入导致数量不等于目标，进行调整
    if len(result_df) != target_count:
        if len(result_df) > target_count:
            # 随机删除多余的
            result_df = result_df.sample(n=target_count, random_state=42)
        else:
            # 随机补充不足的（从原数据中）
            additional_needed = target_count - len(result_df)
            remaining_df = df[~df.index.isin(result_df.index)]
            additional_samples = remaining_df.sample(n=min(additional_needed, len(remaining_df)), random_state=42)
            result_df = pd.concat([result_df, additional_samples], ignore_index=True)
    
    return result_df

# 使用示例
if __name__ == "__main__":
    input_file = "/Users/chenyaxin/Desktop/信息规范/文本分类/合并结果_去重后.xlsx"
    output_file = "/Users/chenyaxin/Desktop/信息规范/文本分类/平衡后的数据集.xlsx"
    
    try:
        balanced_data = balance_dataset_with_distribution(input_file, output_file)
        print("数据处理完成！")
    except Exception as e:
        print(f"处理过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
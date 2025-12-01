import pandas as pd
import os
import glob

def merge_and_analyze_financial_literacy(folder_path):
    """
    合并指定文件夹中金融素养分类Excel文件并统计分类分布
    
    Parameters:
    folder_path (str): 包含Excel文件的文件夹路径
    """
    # 确保文件夹路径存在
    if not os.path.exists(folder_path):
        print(f"错误：文件夹路径 '{folder_path}' 不存在")
        return None, None
    
    # 构建完整的文件搜索路径
    search_pattern = os.path.join(folder_path, "金融素养分类*.xlsx")
    files = glob.glob(search_pattern)
    
    # 如果没有找到文件，尝试搜索xls格式
    if not files:
        search_pattern = os.path.join(folder_path, "金融素养分类*.xls")
        files = glob.glob(search_pattern)
    
    if not files:
        print(f"在文件夹 '{folder_path}' 中未找到以'金融素养分类'开头的Excel文件")
        print("支持的文件格式: .xlsx, .xls")
        return None, None
    
    print(f"在文件夹 '{folder_path}' 中找到 {len(files)} 个文件:")
    for i, file in enumerate(files, 1):
        print(f"  {i}. {os.path.basename(file)}")
    
    # 读取并合并所有文件
    all_data = []
    successful_files = 0
    
    for file in files:
        try:
            df = pd.read_excel(file)
            # 添加文件名列以便追踪来源（可选）
            df['source_file'] = os.path.basename(file)
            all_data.append(df)
            successful_files += 1
            print(f"✓ 成功读取: {os.path.basename(file)} (共{len(df)}行)")
        except Exception as e:
            print(f"✗ 读取文件 {os.path.basename(file)} 时出错: {e}")
    
    if not all_data:
        print("没有成功读取任何文件")
        return None, None
    
    # 合并数据
    merged_df = pd.concat(all_data, ignore_index=True)
    print(f"\n合并统计:")
    print(f"  - 成功读取文件: {successful_files}/{len(files)} 个")
    print(f"  - 总数据行数: {len(merged_df)} 行")
    print(f"  - 总列数: {len(merged_df.columns)} 列")
    
    # 显示所有列名
    print(f"  - 所有列名: {list(merged_df.columns)}")
    
    # 检查category_name列是否存在
    if 'category_name' not in merged_df.columns:
        print("\n错误：找不到 'category_name' 列")
        # 显示最可能的相关列
        possible_columns = [col for col in merged_df.columns if 'categor' in col.lower() or '分类' in col or 'type' in col.lower()]
        if possible_columns:
            print("可能的相关列:", possible_columns)
        return merged_df, None
    
    # 统计category_name的分布
    category_distribution = merged_df['category_name'].value_counts()
    
    print("\n金融素养分类统计分布:")
    print("=" * 50)
    total_count = len(merged_df)
    for category, count in category_distribution.items():
        percentage = (count / total_count) * 100
        print(f"  {category}: {count:>4} 个 ({percentage:>6.2f}%)")
    
    print(f"\n汇总:")
    print(f"  - 总样本数: {total_count} 个")
    print(f"  - 分类种类数: {len(category_distribution)} 种")
    
    # 保存合并后的文件
    output_file = os.path.join(folder_path, "金融素养分类_合并结果.xlsx")
    try:
        merged_df.to_excel(output_file, index=False)
        print(f"\n✓ 合并后的文件已保存为: {output_file}")
    except Exception as e:
        print(f"\n✗ 保存文件时出错: {e}")
    
    return merged_df, category_distribution

# 使用方法：直接在代码中指定路径
if __name__ == "__main__":
    # 请将下面的路径替换为您的实际文件夹路径
    # Mac路径示例：
    folder_path = "/Users/chenyaxin/Desktop/审稿修改/分类数据"  # 替换为您的实际路径
    
    print("金融素养分类文件合并与统计分析")
    print("=" * 50)
    print(f"指定文件夹: {folder_path}")
    
    merged_data, distribution = merge_and_analyze_financial_literacy(folder_path)
    
    if merged_data is not None:
        print("\n✓ 分析完成！")
    else:
        print("\n✗ 分析失败！")
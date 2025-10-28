import pandas as pd
import os
from pathlib import Path

def merge_and_analyze_excel_files(folder_path):
    """
    合并文件夹中的Excel文件，去重并统计分类结果
    
    Parameters:
    folder_path: 包含Excel文件的文件夹路径
    """
    
    # 获取文件夹路径
    folder = Path(folder_path)
    
    # 查找所有Excel文件
    excel_files = list(folder.glob("*.xlsx")) + list(folder.glob("*.xls"))
    
    if not excel_files:
        print("在指定文件夹中未找到Excel文件")
        return
    
    print(f"找到 {len(excel_files)} 个Excel文件:")
    for file in excel_files:
        print(f"  - {file.name}")
    
    # 读取并合并所有Excel文件
    all_data = []
    for file in excel_files:
        try:
            df = pd.read_excel(file, engine='openpyxl')
            df['来源文件'] = file.name  # 添加来源文件列
            all_data.append(df)
            print(f"成功读取: {file.name} (共{len(df)}行)")
        except Exception as e:
            print(f"读取文件 {file.name} 时出错: {e}")
    
    if not all_data:
        print("没有成功读取任何文件")
        return
    
    # 合并数据
    merged_df = pd.concat(all_data, ignore_index=True)
    print(f"\n合并后总行数: {len(merged_df)}")
    
    # 根据"发起投诉内容"去重
    before_dedup = len(merged_df)
    merged_df = merged_df.drop_duplicates(subset=['发起投诉内容'], keep='first')
    after_dedup = len(merged_df)
    
    print(f"去重后行数: {after_dedup}")
    print(f"删除重复项: {before_dedup - after_dedup} 行")
    
    # 检查是否存在分类结果列
    classification_column = '分类结果_qwen'
    if classification_column not in merged_df.columns:
        print(f"\n警告: 未找到列 '{classification_column}'")
        print("可用列:", list(merged_df.columns))
    else:
        # 统计分类结果
        category_counts = merged_df[classification_column].value_counts()
        total_classified = category_counts.sum()
        
        print(f"\n分类结果统计 (共{total_classified}条已分类数据):")
        print("=" * 50)
        for category, count in category_counts.items():
            percentage = (count / total_classified) * 100
            print(f"{category}: {count} 条 ({percentage:.1f}%)")
    
    # 保存合并后的文件
    output_file = folder / "合并结果_去重后.xlsx"
    try:
        merged_df.to_excel(output_file, index=False, engine='openpyxl')
        print(f"\n合并后的文件已保存为: {output_file}")
        
        # 保存统计结果到文本文件
        stats_file = folder / "分类统计结果.txt"
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write("分类结果统计\n")
            f.write("=" * 30 + "\n")
            if classification_column in merged_df.columns:
                for category, count in category_counts.items():
                    percentage = (count / total_classified) * 100
                    f.write(f"{category}: {count} 条 ({percentage:.1f}%)\n")
            f.write(f"\n总数据量: {len(merged_df)} 条\n")
            f.write(f"来源文件: {[f.name for f in excel_files]}\n")
        
        print(f"统计结果已保存为: {stats_file}")
        
    except Exception as e:
        print(f"保存文件时出错: {e}")
    
    return merged_df

# 使用示例
if __name__ == "__main__":
    # 设置包含Excel文件的文件夹路径
    folder_path = "/Users/chenyaxin/Desktop/信息规范/文本分类"  # 请修改为您的实际路径
    
    # 执行合并和分析
    result_df = merge_and_analyze_excel_files(folder_path)
    
    if result_df is not None:
        print(f"\n处理完成！")
        print(f"最终数据形状: {result_df.shape}")